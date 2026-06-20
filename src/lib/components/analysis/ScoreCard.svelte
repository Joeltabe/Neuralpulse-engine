<script lang="ts">
  import DoughnutChart from '$lib/components/charts/DoughnutChart.svelte';
  import { classNames } from '$lib/utils/formatters';

  let { label = '', value = 0, color = '#4d6cf5', sublabel = '' } = $props();
</script>

<div class="glass rounded-xl p-4 flex items-center gap-4 card-hover">
  <div class="w-20 h-20 shrink-0">
    <DoughnutChart {value} {color} />
  </div>
  <div class="min-w-0">
    <p class="text-sm font-medium text-white/70">{label}</p>
    <p class={classNames('text-lg font-bold', value >= 0.7 ? 'text-emerald-400' : value >= 0.45 ? 'text-dopamine-400' : 'text-red-400')}>
      {(value * 100).toFixed(1)}%
    </p>
    {#if sublabel}
      <p class="text-xs text-white/40 mt-0.5">{sublabel}</p>
    {/if}
  </div>
</div>
