<script lang="ts">
  import { severityColor } from '$lib/utils/formatters';
  import type { RankedRecommendation } from '$lib/utils/RecommendationEngine';

  let { recommendations = [] as RankedRecommendation[], onRegionHover = (_region: string) => {} } = $props();
  let expandedId = $state('');

  function toggleExpand(id: string) {
    expandedId = expandedId === id ? '' : id;
  }

  function handleRegionHover(region: string) {
    onRegionHover(region);
  }

  function handleRegionLeave() {
    onRegionHover('');
  }

  const severityIcon: Record<string, string> = {
    critical: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z',
    moderate: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z',
    suggestion: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z'
  };

  const severityStyle: Record<string, { border: string; bg: string; text: string; dot: string; glow: string }> = {
    critical: { border: 'border-red-500/30', bg: 'bg-red-500/8', text: 'text-red-400', dot: 'bg-red-400', glow: 'shadow-red-500/20' },
    moderate: { border: 'border-amber-500/30', bg: 'bg-amber-500/8', text: 'text-amber-400', dot: 'bg-amber-400', glow: 'shadow-amber-500/20' },
    suggestion: { border: 'border-blue-500/30', bg: 'bg-blue-500/8', text: 'text-blue-400', dot: 'bg-blue-400', glow: 'shadow-blue-500/20' }
  };

  const regionColors: Record<string, string> = {
    frontal: '#4d6cf5',
    temp: '#10b981',
    pariet: '#8b5cf6',
    occipit: '#06b6d4',
    cereb: '#f59e0b',
    corpus: '#ec4899',
    stem: '#ef4444',
    pitua: '#a855f7'
  };
</script>

<div class="rec-list space-y-3">
  {#each recommendations as rec, i}
    {@const style = severityStyle[rec.severity] || severityStyle.suggestion}
    {@const isExpanded = expandedId === `rec-${i}`}
    <div
      class="rec-card rounded-xl border {style.border} {style.bg} overflow-hidden transition-all duration-300"
      class:shadow-lg={isExpanded}
      style="animation: rec-slide-in 0.4s {i * 0.06}s ease-out both;"
    >
      <!-- Main content -->
      <div
        class="w-full text-left p-4 flex items-start gap-3 cursor-pointer"
        onclick={() => toggleExpand(`rec-${i}`)}
        role="button"
        tabindex="0"
        onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggleExpand(`rec-${i}`); }}
      >
        <!-- Rank badge -->
        <div class="flex flex-col items-center gap-1 shrink-0 pt-0.5">
          <span class="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[10px] font-bold text-white/50">
            {rec.rank}
          </span>
          <svg class="w-3.5 h-3.5 {style.text}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d={severityIcon[rec.severity] || severityIcon.suggestion} />
          </svg>
        </div>

        <div class="flex-1 min-w-0">
          <!-- Severity + Category -->
          <div class="flex items-center gap-2 mb-1.5">
            <span class="text-[10px] font-bold uppercase tracking-wider {style.text}">{rec.severity}</span>
            <span class="text-[10px] text-white/25">•</span>
            <span class="text-[10px] text-white/30 uppercase tracking-wider">{rec.category}</span>
          </div>

          <!-- Title -->
          <h4 class="text-sm font-semibold text-white/90 leading-snug">{rec.title}</h4>

          <!-- Brain region badges -->
          {#if rec.affected_regions?.length}
            <div class="flex flex-wrap gap-1 mt-2">
              {#each rec.affected_regions as region}
              <span
                  class="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-medium border transition-all duration-200 hover:scale-105 cursor-pointer"
                  style="background: {regionColors[region.key] || '#666'}10; border-color: {regionColors[region.key] || '#666'}30; color: {regionColors[region.key] || '#999'};"
                  onmouseenter={() => handleRegionHover(region.key)}
                  onmouseleave={() => handleRegionLeave()}
                  role="button"
                  tabindex="0"
                >
                  <span
                    class="w-1 h-1 rounded-full"
                    style="background: {regionColors[region.key] || '#666'}; box-shadow: 0 0 3px {regionColors[region.key] || '#666'};"
                  ></span>
                  {region.name}
                  <span class="text-white/30">{Math.round(region.activation * 100)}%</span>
                </span>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Impact score -->
        <div class="shrink-0 text-right flex flex-col items-end gap-1">
          <span class="text-[10px] text-white/30 uppercase tracking-wider">Impact</span>
          <div class="flex items-center gap-1">
            <div class="w-12 h-1.5 rounded-full bg-white/5 overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-700 ease-out"
                style="width: {rec.neural_impact_score * 100}%; background: linear-gradient(90deg, {style.text === 'text-red-400' ? '#ef4444' : style.text === 'text-amber-400' ? '#f59e0b' : '#3b82f6'}80, {style.text === 'text-red-400' ? '#ef4444' : style.text === 'text-amber-400' ? '#f59e0b' : '#3b82f6'});"
              ></div>
            </div>
            <span class="text-xs font-bold text-white/60 tabular-nums">{(rec.neural_impact_score * 100).toFixed(0)}%</span>
          </div>
          <!-- Chevron -->
          <svg class="w-3.5 h-3.5 text-white/20 transition-transform duration-300 mt-1" class:rotate-180={isExpanded} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>

      <!-- Expanded detail panel -->
      {#if isExpanded}
        <div class="px-4 pb-4 pt-0 border-t border-white/5" style="animation: expand-in 0.3s ease-out;">
          <!-- Description -->
          <p class="text-xs text-white/50 leading-relaxed mt-3">{rec.description}</p>

          <!-- Suggestion (the fix) -->
          <div class="mt-3 rounded-lg bg-white/[0.04] border border-white/5 p-3">
            <div class="flex items-center gap-1.5 mb-1.5">
              <svg class="w-3 h-3 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span class="text-[10px] font-bold text-emerald-400 uppercase tracking-wider">How to Fix</span>
            </div>
            <p class="text-xs text-white/60 leading-relaxed">{rec.suggestion}</p>
          </div>

          <!-- Why this recommendation -->
          {#if rec.why}
            <div class="mt-3 rounded-lg bg-white/[0.03] border border-white/5 p-3">
              <div class="flex items-center gap-1.5 mb-1.5">
                <svg class="w-3 h-3 text-neural-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span class="text-[10px] font-bold text-neural-400 uppercase tracking-wider">Why This</span>
              </div>
              <p class="text-[11px] text-white/40 leading-relaxed">{rec.why}</p>
            </div>
          {/if}

          <!-- Signal breakdown mini-bars -->
          {#if rec.signal_breakdown}
            <div class="mt-3 grid grid-cols-5 gap-1.5">
              {#each [
                { key: 'attention_signal', label: 'ATT', color: '#4d6cf5' },
                { key: 'dopamine_signal', label: 'DOP', color: '#f59e0b' },
                { key: 'memory_signal', label: 'MEM', color: '#10b981' },
                { key: 'temporal_signal', label: 'TIME', color: '#8b5cf6' },
                { key: 'pacing_signal', label: 'PACE', color: '#06b6d4' }
              ] as signal}
                {@const val = rec.signal_breakdown[signal.key as keyof typeof rec.signal_breakdown] ?? 0}
                <div class="text-center">
                  <div class="h-8 bg-white/[0.03] rounded overflow-hidden flex items-end justify-center relative">
                    <div
                      class="w-full rounded-t transition-all duration-500"
                      style="height: {val * 100}%; background: {signal.color}40;"
                    ></div>
                  </div>
                  <span class="text-[8px] text-white/25 font-medium mt-0.5 block">{signal.label}</span>
                </div>
              {/each}
            </div>
          {/if}

          <!-- Timestamp anchor -->
          {#if rec.timestamp_sec > 0}
            <div class="mt-3 flex items-center gap-1.5">
              <svg class="w-3 h-3 text-white/25" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span class="text-[10px] text-white/30">Focus point at <strong class="text-white/50">{rec.timestamp_sec.toFixed(1)}s</strong></span>
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/each}

  {#if recommendations.length === 0}
    <div class="text-center py-8">
      <svg class="w-8 h-8 mx-auto text-white/15 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <p class="text-xs text-white/30">No recommendations — your content is performing well</p>
    </div>
  {/if}
</div>

<style>
  @keyframes rec-slide-in {
    from { opacity: 0; transform: translateX(-12px); }
    to { opacity: 1; transform: translateX(0); }
  }

  @keyframes expand-in {
    from { opacity: 0; max-height: 0; }
    to { opacity: 1; max-height: 500px; }
  }

  .rec-card {
    backdrop-filter: blur(4px);
  }

  .rec-card:hover {
    background: rgba(255, 255, 255, 0.04);
  }
</style>
