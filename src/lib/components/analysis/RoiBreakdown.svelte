<script lang="ts">
  import { formatPercent } from '$lib/utils/formatters';

  let { roi_breakdown = {} as Record<string, number>, color = '#4d6cf5' } = $props();

  let entries = $derived(Object.entries(roi_breakdown).sort((a, b) => b[1] - a[1]));
</script>

<div class="space-y-2">
  {#each entries as [roi, score]}
    <div class="flex items-center gap-3">
      <span class="text-xs font-medium text-white/60 w-12 shrink-0">{roi}</span>
      <div class="flex-1 h-2 rounded-full bg-white/5 overflow-hidden">
        <div
          class="h-full rounded-full transition-all duration-1000 ease-out"
          style="width: {Math.max(1, score * 100)}%; background: {color};"
        ></div>
      </div>
      <span class="text-xs font-mono text-white/50 w-12 text-right">{formatPercent(score, 0)}</span>
    </div>
  {/each}
</div>
