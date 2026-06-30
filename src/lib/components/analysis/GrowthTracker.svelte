<script lang="ts">
  import Card from '$lib/components/ui/Card.svelte';
  import FrameFingerprintViewer from '$lib/components/analysis/FrameFingerprintViewer.svelte';
  import type { ContentIdentity, BrainScores } from '$lib/types/api';

  let { identity, currentScores }: { identity: ContentIdentity; currentScores: BrainScores } = $props();

  let expanded = $state(false);

  const journeyIcons: Record<string, string> = {
    exact: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z',
    perceptual: 'M13 10V3L4 14h7v7l9-11h-7z',
    derivative: 'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
    reordered: 'M4 6h16M4 12h16M4 18h12M4 6l4 4M4 6l4-4',
    partial: 'M13 7h8m0 0v8m0-8l-8 8-4-4-6 6',
    new: 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
  };

  const journeyLabels: Record<string, string> = {
    exact: 'Same Version',
    perceptual: 'Improved Version',
    derivative: 'Reimagined Content',
    reordered: 'Rearranged Edit',
    partial: 'Content Segment',
    new: 'First Analysis',
  };

  const journeyDescriptions: Record<string, string> = {
    exact: 'This is the same version you analyzed before — scores are identical. No changes detected.',
    perceptual: 'You re-encoded or reformatted your content since last analysis. Small quality changes detected.',
    derivative: 'You transformed your original content — cropped, filtered, or overlaid new elements. Scores may differ.',
    reordered: 'You rearranged your clips. The system recognizes your editing pattern and tracks the new arrangement.',
    partial: 'This content shares segments with a previous analysis. Your content library is growing!',
    new: 'First time we\'ve seen this content. Your baseline scores are recorded for future comparison.',
  };

  const journeyColor = (t: string) =>
    t === 'exact' ? 'text-emerald-400 bg-emerald-500/15 border-emerald-500/20' :
    t === 'perceptual' ? 'text-blue-400 bg-blue-500/15 border-blue-500/20' :
    t === 'derivative' ? 'text-violet-400 bg-violet-500/15 border-violet-500/20' :
    t === 'reordered' ? 'text-amber-400 bg-amber-500/15 border-amber-500/20' :
    t === 'partial' ? 'text-cyan-400 bg-cyan-500/15 border-cyan-500/20' :
    'text-emerald-400 bg-emerald-500/15 border-emerald-500/20';

  let matchedFrameCount = $derived(
    identity.frame_signatures.filter(f => f.similarity_to_reference !== null && f.similarity_to_reference > 0.5).length
  );

  let matchCoverage = $derived(
    identity.frame_signatures.length > 0
      ? matchedFrameCount / identity.frame_signatures.length
      : identity.temporal_match_coverage
  );

  function deltaColor(d: number): string {
    if (d > 0.05) return 'text-emerald-400';
    if (d < -0.05) return 'text-red-400';
    return 'text-white/40';
  }

  function deltaArrow(d: number): string {
    if (d > 0.05) return '\u2191';
    if (d < -0.05) return '\u2193';
    return '\u2192';
  }
</script>

<Card>
  <div class="flex items-center gap-3">
    <div class="w-8 h-8 rounded-lg {identity.is_known_content ? 'bg-blue-500/15' : 'bg-emerald-500/15'} flex items-center justify-center shrink-0">
      <svg class="w-4 h-4 {identity.is_known_content ? 'text-blue-400' : 'text-emerald-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={identity.is_known_content ? 'M13 10V3L4 14h7v7l9-11h-7z' : 'M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'} />
      </svg>
    </div>
    <div class="flex-1">
      <div class="flex items-center gap-2">
        <span class="text-sm font-semibold {identity.is_known_content ? 'text-blue-400' : 'text-emerald-400'}">
          {identity.is_known_content ? 'Content Journey' : 'First Analysis'}
        </span>
        <span class="text-[9px] px-1.5 py-0.5 rounded font-medium {journeyColor(identity.match_type)}">
          {journeyLabels[identity.match_type] || identity.match_type}
        </span>
      </div>
      <p class="text-[10px] text-white/40 mt-0.5">{journeyDescriptions[identity.match_type] || identity.match_details}</p>
    </div>
    {#if identity.is_known_content && identity.confidence > 0}
      <div class="text-right shrink-0">
        <div class="flex items-center gap-1.5">
          <div class="w-12 h-1.5 rounded-full bg-white/5 overflow-hidden">
            <div class="h-full rounded-full bg-blue-500/60" style="width: {identity.confidence * 100}%"></div>
          </div>
          <span class="text-xs font-bold text-blue-400 tabular-nums">{(identity.confidence * 100).toFixed(0)}%</span>
        </div>
        <p class="text-[9px] text-white/30 mt-0.5">content match</p>
      </div>
    {/if}
  </div>

  {#if identity.is_known_content}
    <div class="flex flex-wrap items-center gap-3 mt-3 text-[10px] text-white/40">
      {#if identity.first_filename}
        <span>Original: <span class="text-white/60 font-medium">{identity.first_filename}</span></span>
      {/if}
      {#if identity.first_analysis_grade}
        <span>Previous score: <span class="text-white/60 font-medium">{identity.first_analysis_grade}</span></span>
      {/if}
      {#if identity.first_seen_at}
        <span>First analyzed: <span class="text-white/60 font-medium">{identity.first_seen_at}</span></span>
      {/if}
      {#if identity.frame_signatures.length > 0}
        <span>Frames tracked: <span class="text-white/60 font-medium">{matchedFrameCount}/{identity.frame_signatures.length}</span></span>
      {/if}
      {#if identity.alignment}
        <span>Match ratio: <span class="text-white/60 font-medium">{(identity.alignment.coverage_ratio * 100).toFixed(0)}%</span></span>
      {/if}
    </div>

    <!-- Frame fingerprint heatmap -->
    {#if identity.frame_signatures.length > 0}
      <div class="mt-3">
        <FrameFingerprintViewer
          frameSignatures={identity.frame_signatures}
          temporalMatches={identity.temporal_matches}
          alignment={identity.alignment}
        />
      </div>
    {/if}

    <!-- Score comparison: how your changes impacted performance -->
    {#if identity.previous_scores && identity.score_changes}
      <button
        onclick={() => expanded = !expanded}
        class="w-full flex items-center gap-2 mt-3 px-3 py-2 rounded-lg bg-white/[0.02] hover:bg-white/[0.04] transition-colors border border-white/5"
      >
        <svg class="w-3.5 h-3.5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
        <span class="flex-1 text-[11px] text-white/50">How your edits changed performance</span>
        <svg class="w-3 h-3 text-white/20 transition-transform {expanded ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {#if expanded}
        <div class="mt-2 space-y-2" style="animation: expand-in 0.2s ease-out;">
          {#each [
            { label: 'Attention', current: currentScores.attention.overall, previous: identity.previous_scores.attention, delta: identity.score_changes.attention_delta },
            { label: 'Dopamine', current: currentScores.dopamine.overall, previous: identity.previous_scores.dopamine, delta: identity.score_changes.dopamine_delta },
            { label: 'Memory', current: currentScores.memory.overall, previous: identity.previous_scores.memory, delta: identity.score_changes.memory_delta },
          ] as dim}
            <div class="rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
              <div class="flex items-center gap-3">
                <span class="text-[10px] font-medium text-white/60 w-16">{dim.label}</span>
                <div class="flex-1 space-y-1">
                  <div class="flex items-center gap-2">
                    <span class="text-[9px] text-white/30 w-14">Before</span>
                    <div class="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div class="h-full rounded-full bg-white/20" style="width: {dim.previous * 100}%"></div>
                    </div>
                    <span class="text-[10px] font-mono text-white/40 w-10 text-right tabular-nums">{(dim.previous * 100).toFixed(0)}%</span>
                  </div>
                  <div class="flex items-center gap-2">
                    <span class="text-[9px] text-white/30 w-14">After</span>
                    <div class="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                      <div class="h-full rounded-full {dim.delta > 0.05 ? 'bg-emerald-500/60' : dim.delta < -0.05 ? 'bg-red-500/60' : 'bg-white/30'}" style="width: {dim.current * 100}%"></div>
                    </div>
                    <span class="text-[10px] font-mono text-white/60 w-10 text-right tabular-nums">{(dim.current * 100).toFixed(0)}%</span>
                  </div>
                </div>
                <div class="shrink-0 text-right">
                  <span class="text-[10px] font-bold tabular-nums {deltaColor(dim.delta)}">
                    {deltaArrow(dim.delta)} {(dim.delta * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          {/each}

          <div class="rounded-lg bg-white/[0.02] border border-white/5 p-2.5">
            <p class="text-[9px] text-white/40 uppercase tracking-wider mb-1">Change Summary</p>
            <p class="text-[10px] text-white/50 leading-relaxed">{identity.match_details}</p>
          </div>

          {#if identity.alignment}
            <div class="grid grid-cols-4 gap-2">
              {#each [
                { label: 'Frame Match', value: (identity.alignment.coverage_ratio * 100).toFixed(0) + '%' },
                { label: 'Longest Segment', value: identity.alignment.longest_match_segment_sec.toFixed(1) + 's' },
                { label: 'Reordered', value: identity.alignment.reordered_segments > 0 ? identity.alignment.reordered_segments + ' segs' : 'None' },
                { label: 'Alignment', value: identity.alignment.offset_frames + ' frames' },
              ] as stat}
                <div class="rounded-lg bg-white/[0.02] border border-white/5 p-1.5 text-center">
                  <p class="text-[8px] text-white/30 uppercase">{stat.label}</p>
                  <p class="text-[11px] font-bold text-white/70">{stat.value}</p>
                </div>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    {/if}
  {/if}
</Card>

<style>
  @keyframes expand-in {
    from { opacity: 0; }
    to { opacity: 1; }
  }
</style>
