import type { FrameSignature, TemporalMatchSegment, FrameAlignmentResult, ContentIdentity } from '$lib/types/api';

/** Hamming distance between two perceptual hash hex strings */
function hammingDistance(h1: string, h2: string): number {
  const maxLen = Math.max(h1.length, h2.length);
  let dist = 0;
  for (let i = 0; i < maxLen; i++) {
    const c1 = parseInt(h1[i] || '0', 16);
    const c2 = parseInt(h2[i] || '0', 16);
    let xor = c1 ^ c2;
    while (xor) { dist += xor & 1; xor >>= 1; }
  }
  return dist;
}

/** Similarity score [0-1] from hamming distance */
export function hashSimilarity(h1: string, h2: string): number {
  const maxBits = Math.max(h1.length, h2.length) * 4;
  if (maxBits === 0) return 0;
  return 1 - hammingDistance(h1, h2) / maxBits;
}

function cosineSimilarity(a: number[], b: number[]): number {
  let dot = 0, na = 0, nb = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    na += a[i] * a[i];
    nb += b[i] * b[i];
  }
  const denom = Math.sqrt(na) * Math.sqrt(nb);
  return denom === 0 ? 0 : dot / denom;
}

export function frameSimilarity(
  a: FrameSignature,
  b: FrameSignature,
  opts?: { embeddingWeight?: number; hashWeight?: number }
): number {
  const ew = opts?.embeddingWeight ?? 0.4;
  const hw = opts?.hashWeight ?? 0.6;
  const hashSim = hashSimilarity(a.perceptual_hash, b.perceptual_hash);
  if (a.dino_embedding && b.dino_embedding && a.dino_embedding.length > 0 && b.dino_embedding.length > 0) {
    const embSim = cosineSimilarity(a.dino_embedding, b.dino_embedding);
    return hw * hashSim + ew * embSim;
  }
  return hashSim;
}

export interface AlignmentWindow {
  offset: number;
  score: number;
  matched: number[];
}

/** Slide `query` across `reference` to find the best temporal alignment */
export function findBestAlignment(
  query: FrameSignature[],
  reference: FrameSignature[],
  threshold = 0.75
): AlignmentWindow {
  let best: AlignmentWindow = { offset: 0, score: 0, matched: [] };
  if (query.length === 0 || reference.length === 0) return best;

  const searchRange = reference.length;
  for (let offset = -searchRange; offset <= searchRange; offset++) {
    let scoreSum = 0;
    let count = 0;
    const matched: number[] = [];

    for (let qi = 0; qi < query.length; qi++) {
      const ri = qi + offset;
      if (ri < 0 || ri >= reference.length) continue;
      const sim = frameSimilarity(query[qi], reference[ri]);
      if (sim >= threshold) {
        scoreSum += sim;
        count++;
        matched.push(qi);
      }
    }

    const avgScore = count > 0 ? scoreSum / count : 0;
    if (avgScore > best.score || (avgScore === best.score && count > best.matched.length)) {
      best = { offset, score: avgScore, matched };
    }
  }

  return best;
}

/** Extract contiguous matched runs from a boolean array */
function findContiguousRuns(matched: boolean[]): { start: number; end: number }[] {
  const runs: { start: number; end: number }[] = [];
  let i = 0;
  while (i < matched.length) {
    if (matched[i]) {
      const start = i;
      while (i < matched.length && matched[i]) i++;
      runs.push({ start, end: i - 1 });
    } else {
      i++;
    }
  }
  return runs;
}

/** Detect if frames appear in a different order than the reference */
function detectReordering(
  queryIndices: number[],
  alignmentOffset: number
): number {
  if (queryIndices.length < 3) return 0;
  let inversions = 0;
  for (let i = 0; i < queryIndices.length; i++) {
    for (let j = i + 1; j < queryIndices.length; j++) {
      const ri = queryIndices[i] + alignmentOffset;
      const rj = queryIndices[j] + alignmentOffset;
      if (ri > rj) inversions++;
    }
  }
  const totalPairs = (queryIndices.length * (queryIndices.length - 1)) / 2;
  return totalPairs > 0 ? inversions / totalPairs : 0;
}

export function analyzeTemporalMatch(
  query: FrameSignature[],
  reference: FrameSignature[],
  similarityThreshold = 0.7
): {
  segments: TemporalMatchSegment[];
  alignment: FrameAlignmentResult;
} {
  const best = findBestAlignment(query, reference, similarityThreshold);
  const matchedFlags: boolean[] = query.map(() => false);
  const segmentSimilarities: number[] = [];

  for (let qi = 0; qi < query.length; qi++) {
    const ri = qi + best.offset;
    if (ri < 0 || ri >= reference.length) continue;
    const sim = frameSimilarity(query[qi], reference[ri]);
    if (sim >= similarityThreshold) {
      matchedFlags[qi] = true;
      segmentSimilarities.push(sim);
    }
  }

  const runs = findContiguousRuns(matchedFlags);
  const matchedCount = matchedFlags.filter(Boolean).length;
  const queryFrames = query;
  const reorderRatio = detectReordering(best.matched, best.offset);

  const segments: TemporalMatchSegment[] = runs.map((run) => {
    const sims = [];
    for (let f = run.start; f <= run.end; f++) {
      const ri = f + best.offset;
      if (ri >= 0 && ri < reference.length) {
        sims.push(frameSimilarity(queryFrames[f], reference[ri]));
      }
    }
    const avgSim = sims.length > 0 ? sims.reduce((a, b) => a + b, 0) / sims.length : 0;
    const matchType: TemporalMatchSegment['match_type'] =
      avgSim > 0.92 ? 'exact' : avgSim > 0.75 ? 'near_duplicate' : 'modified';

    return {
      start_frame: run.start,
      end_frame: run.end,
      start_sec: queryFrames[run.start]?.timestamp_sec ?? 0,
      end_sec: queryFrames[run.end]?.timestamp_sec ?? 0,
      match_confidence: avgSim,
      match_type: matchType,
      reference_segment: null,
    };
  });

  const coverage = query.length > 0 ? matchedCount / query.length : 0;
  const avgSimilarity = segmentSimilarities.length > 0
    ? segmentSimilarities.reduce((a, b) => a + b, 0) / segmentSimilarities.length
    : 0;

  // Find longest run
  let longestRun = 0;
  for (const run of runs) {
    const len = run.end - run.start + 1;
    if (len > longestRun) longestRun = len;
  }
  const longestMatchSec = queryFrames.length > 0 && longestRun > 0
    ? longestRun * (queryFrames[1]?.timestamp_sec - queryFrames[0]?.timestamp_sec || 1)
    : 0;

  const alignment: FrameAlignmentResult = {
    alignment_score: best.score,
    offset_frames: best.offset,
    matched_frame_count: matchedCount,
    total_frame_count: query.length,
    coverage_ratio: coverage,
    longest_match_segment_sec: longestMatchSec,
    reordered_segments: reorderRatio > 0.15 ? Math.round(reorderRatio * runs.length) : 0,
  };

  return { segments, alignment };
}

/** Compute a single frame signature against a reference array to find the best match */
export function findBestFrameMatch(
  frame: FrameSignature,
  reference: FrameSignature[]
): { index: number; similarity: number } {
  let bestIdx = -1;
  let bestSim = 0;
  for (let i = 0; i < reference.length; i++) {
    const sim = frameSimilarity(frame, reference[i]);
    if (sim > bestSim) {
      bestSim = sim;
      bestIdx = i;
    }
  }
  return { index: bestIdx, similarity: bestSim };
}

/** Compute overall classification from raw match data */
export function classifyMatch(
  coverage: number,
  avgSimilarity: number,
  reorderCount: number,
  longestSegmentSec: number,
  totalDurationSec: number
): ContentIdentity['match_type'] {
  if (coverage > 0.95 && avgSimilarity > 0.92) return 'exact';
  if (coverage > 0.8 && avgSimilarity > 0.75) return 'perceptual';
  if (reorderCount > 0) return 'reordered';
  if (coverage > 0.15) return 'derivative';
  if (coverage > 0.05) return 'partial';
  return 'new';
}
