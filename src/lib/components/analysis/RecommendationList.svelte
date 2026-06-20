<script lang="ts">
  import { severityColor } from '$lib/utils/formatters';
  import type { Recommendation } from '$lib/types/api';

  let { recommendations = [] as Recommendation[] } = $props();
</script>

<div class="space-y-2">
  {#each recommendations as rec}
    <div class={`rounded-xl border p-4 ${severityColor(rec.severity)}`}>
      <div class="flex items-start justify-between gap-2">
        <div class="min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-semibold uppercase tracking-wider">{rec.severity}</span>
            <span class="text-xs text-white/30">{rec.category}</span>
          </div>
          <h4 class="text-sm font-semibold">{rec.title}</h4>
          <p class="text-sm text-white/60 mt-0.5">{rec.description}</p>
          <p class="text-sm text-white/50 mt-1 italic">{rec.suggestion}</p>
        </div>
        <div class="shrink-0 text-right">
          <span class="text-xs text-white/40">Impact</span>
          <p class="text-sm font-semibold">{(rec.expected_impact * 100).toFixed(0)}%</p>
        </div>
      </div>
      {#if rec.timestamp_sec > 0}
        <p class="text-xs text-white/30 mt-1">at {rec.timestamp_sec.toFixed(1)}s</p>
      {/if}
    </div>
  {/each}
</div>
