<script lang="ts">
  import type { FrameSignature, TemporalMatchSegment, FrameAlignmentResult } from '$lib/types/api';
  import { frameSimilarity, hashSimilarity } from '$lib/utils/FrameAlignmentEngine';

  let {
    frameSignatures = [] as FrameSignature[],
    temporalMatches = [] as TemporalMatchSegment[],
    alignment = null as FrameAlignmentResult | null,
  } = $props();

  let hoveredFrame = $state<number | null>(null);
  let showSimilarity = $state<'hash' | 'embedding'>('hash');
  let expanded = $state(false);

  const segColors: Record<string, string> = {
    exact: 'bg-emerald-500/70',
    near_duplicate: 'bg-amber-500/60',
    modified: 'bg-orange-500/50',
    reordered: 'bg-rose-500/50',
  };

  const segColorsBorder: Record<string, string> = {
    exact: 'border-emerald-500/40',
    near_duplicate: 'border-amber-500/30',
    modified: 'border-orange-500/30',
    reordered: 'border-rose-500/30',
  };

  const segLabels: Record<string, string> = {
    exact: 'Same',
    near_duplicate: 'Evolved',
    modified: 'Transformed',
    reordered: 'Rearranged',
  };

  let frameCount = $derived(frameSignatures.length);
  let durationSec = $derived(
    frameCount > 1
      ? frameSignatures[frameCount - 1].timestamp_sec - frameSignatures[0].timestamp_sec
      : 0
  );

  // Pre-compute similarities between consecutive frames (scene change detection)
  let sceneChanges = $derived(() => {
    const changes: number[] = [];
    for (let i = 1; i < frameSignatures.length; i++) {
      const sim = hashSimilarity(
        frameSignatures[i - 1].perceptual_hash,
        frameSignatures[i].perceptual_hash
      );
      if (sim < 0.4) changes.push(i);
    }
    return changes;
  });

  function frameColor(sig: FrameSignature): string {
    if (sig.similarity_to_reference === null) return 'bg-white/8';
    const s = sig.similarity_to_reference;
    if (s > 0.92) return 'bg-emerald-500/60';
    if (s > 0.75) return 'bg-amber-500/50';
    if (s > 0.5) return 'bg-orange-500/40';
    return 'bg-red-500/30';
  }

  function formatTime(s: number): string {
    const m = Math.floor(s / 60);
    const sec = Math.floor(s % 60);
    return `${m}:${sec.toString().padStart(2, '0')}`;
  }
</script>

<div class="space-y-2">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2">
      <svg class="w-3.5 h-3.5 text-white/40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
      <span class="text-[10px] text-white/40 uppercase tracking-wider">Content Evolution Heatmap</span>
    </div>

    <div class="flex items-center gap-2">
      <span class="text-[9px] text-white/30">{durationSec.toFixed(0)}s &middot; {frameCount} frames &middot; sample every {frameCount > 1 ? ((frameSignatures[1]?.timestamp_sec - frameSignatures[0]?.timestamp_sec) || 0).toFixed(1) : '?'}s</span>
      <button
        onclick={() => expanded = !expanded}
        class="text-[9px] text-neural-400 hover:text-neural-300 transition-colors"
      >
        {expanded ? 'Less' : 'Detail'}
      </button>
    </div>
  </div>

  <!-- Frame Heatmap -->
  <div
    class="relative w-full h-8 rounded-lg overflow-hidden bg-white/[0.02] cursor-crosshair"
    onmouseleave={() => hoveredFrame = null}
  >
    <!-- Frame bars -->
    {#each frameSignatures as sig, i}
      {@const w = 100 / frameCount}
      {@const isMatched = sig.similarity_to_reference !== null && sig.similarity_to_reference > 0.5}
      {@const isHovered = hoveredFrame === i}
      <div
        class="absolute top-0 h-full transition-all duration-100"
        style="left: {(i / frameCount) * 100}%; width: {w}%; {isHovered ? 'z-index: 10;' : ''}"
        onmouseenter={() => hoveredFrame = i}
      >
        <div
          class="h-full w-full rounded-[1px] transition-all duration-150"
          class:opacity-100={isMatched || isHovered}
          class:opacity-30={!isMatched && !isHovered}
          style="background: {isHovered ? 'rgba(255,255,255,0.15)' : frameColor(sig)}; {isHovered ? 'box-shadow: 0 0 6px rgba(255,255,255,0.2);' : ''}"
        ></div>
      </div>
    {/each}

    <!-- Scene change markers -->
    {#each sceneChanges() as idx}
      <div
        class="absolute top-0 w-px h-full bg-white/30 z-10"
        style="left: {(idx / frameCount) * 100}%"
      ></div>
    {/each}

    <!-- Temporal match segment overlays -->
    {#each temporalMatches as seg}
      <div
        class="absolute top-0 h-full border-t border-b z-5 rounded-sm pointer-events-none"
        style="left: {(seg.start_frame / frameCount) * 100}%; width: {((seg.end_frame - seg.start_frame + 1) / frameCount) * 100}%; {segColorsBorder[seg.match_type] || 'border-white/10'}"
      >
        <div class="h-full w-full rounded-sm {segColors[seg.match_type] || 'bg-white/10'}" style="opacity: {seg.match_confidence * 0.5};"></div>
      </div>
    {/each}
  </div>

  <!-- Hover tooltip -->
  {#if hoveredFrame !== null && frameSignatures[hoveredFrame]}
    {@const sig = frameSignatures[hoveredFrame]}
    <div class="rounded-lg bg-white/[0.04] border border-white/5 p-2.5 text-[10px] space-y-1">
      <div class="flex items-center gap-3">
        <span class="text-white/40">Frame <strong class="text-white/60">#{sig.index}</strong></span>
        <span class="text-white/40">at <strong class="text-white/60">{formatTime(sig.timestamp_sec)}</strong></span>
        {#if sig.scene_boundary}
          <span class="px-1 py-0.5 rounded text-[8px] bg-blue-500/15 text-blue-400 font-medium">Scene Cut</span>
        {/if}
      </div>
      <div class="flex items-center gap-4">
        <span class="text-white/30">pHash: <code class="text-white/50 font-mono">{sig.perceptual_hash.slice(0, 16)}...</code></span>
        {#if sig.similarity_to_reference !== null}
          <span class="text-white/30">Match: <strong class="{sig.similarity_to_reference > 0.75 ? 'text-emerald-400' : sig.similarity_to_reference > 0.5 ? 'text-amber-400' : 'text-red-400'}">{(sig.similarity_to_reference * 100).toFixed(1)}%</strong></span>
        {/if}
        {#if sig.dino_embedding}
          <span class="text-white/30">Emb: <span class="text-white/50">{sig.dino_embedding.length}d</span></span>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Legend -->
  <div class="flex flex-wrap items-center gap-3 text-[9px] text-white/30">
    <div class="flex items-center gap-1">
      <span class="w-2 h-2 rounded-sm bg-emerald-500/60"></span>
      <span>Unchanged</span>
    </div>
    <div class="flex items-center gap-1">
      <span class="w-2 h-2 rounded-sm bg-amber-500/50"></span>
      <span>Evolved</span>
    </div>
    <div class="flex items-center gap-1">
      <span class="w-2 h-2 rounded-sm bg-orange-500/40"></span>
      <span>Transformed</span>
    </div>
    <div class="flex items-center gap-1">
      <span class="w-2 h-2 rounded-sm bg-red-500/30"></span>
      <span>New Content</span>
    </div>
    <div class="flex items-center gap-1">
      <span class="w-0.5 h-3 bg-white/30"></span>
      <span>Scene Cut</span>
    </div>
  </div>

  <!-- Expanded detail: Match segment breakdown -->
  {#if expanded && temporalMatches.length > 0}
    <div class="space-y-1.5 pt-1">
      <p class="text-[9px] text-white/30 uppercase tracking-wider">Match Segments</p>
      {#each temporalMatches as seg, i}
        <div class="rounded-lg border border-white/5 bg-white/[0.02] p-2.5">
          <div class="flex items-center gap-2">
            <span class="text-[8px] px-1 py-0.5 rounded font-medium {segColors[seg.match_type]?.replace('bg-', 'bg-').replace('/70', '/20').replace('/60', '/15').replace('/50', '/15') || 'bg-white/10'} {segColorsBorder[seg.match_type]?.replace('border-', 'border-') || 'border-white/10'} border text-white/70">
              {segLabels[seg.match_type] || seg.match_type}
            </span>
            <span class="text-[10px] text-white/40">
              Frames {seg.start_frame}&ndash;{seg.end_frame}
              <span class="text-white/20"> &middot; </span>
              {formatTime(seg.start_sec)} &ndash; {formatTime(seg.end_sec)}
              <span class="text-white/20"> &middot; </span>
              {(seg.end_sec - seg.start_sec).toFixed(1)}s
            </span>
            <div class="flex-1"></div>
            <div class="flex items-center gap-1">
              <div class="w-12 h-1 rounded-full bg-white/5 overflow-hidden">
                <div class="h-full rounded-full {seg.match_confidence > 0.92 ? 'bg-emerald-500/60' : seg.match_confidence > 0.75 ? 'bg-amber-500/60' : 'bg-orange-500/60'}" style="width: {seg.match_confidence * 100}%"></div>
              </div>
              <span class="text-[9px] font-bold text-white/40 tabular-nums">{(seg.match_confidence * 100).toFixed(0)}%</span>
            </div>
          </div>
          {#if seg.reference_segment}
            <div class="flex items-center gap-2 mt-1 text-[9px] text-white/30">
              <span>Ref: {seg.reference_segment.filename}</span>
              <span>at {formatTime(seg.reference_segment.start_sec)}</span>
            </div>
          {/if}
        </div>
      {/each}
    </div>

    <!-- Alignment summary -->
    {#if alignment}
      <div class="grid grid-cols-4 gap-2 pt-1">
        {#each [
          { label: 'Alignment', value: (alignment.alignment_score * 100).toFixed(0) + '%' },
          { label: 'Coverage', value: (alignment.coverage_ratio * 100).toFixed(0) + '%' },
          { label: 'Matched', value: alignment.matched_frame_count + '/' + alignment.total_frame_count },
          { label: 'Longest', value: alignment.longest_match_segment_sec.toFixed(1) + 's' },
        ] as stat}
          <div class="rounded-lg bg-white/[0.02] border border-white/5 p-1.5 text-center">
            <p class="text-[8px] text-white/30 uppercase">{stat.label}</p>
            <p class="text-[11px] font-bold text-white/70">{stat.value}</p>
          </div>
        {/each}
      </div>
    {/if}
  {/if}
</div>
