<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  let { value = 0, label = '', color = '#4d6cf5', max = 1 } = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart;

  onMount(() => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    chart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        datasets: [{
          data: [value, max - value],
          backgroundColor: [color, 'rgba(255,255,255,0.05)'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '80%',
        animation: { duration: 1000, easing: 'easeOutElastic' },
        plugins: {
          legend: { display: false },
          tooltip: { enabled: false }
        }
      }
    });
  });

  onDestroy(() => chart?.destroy());
</script>

<div class="relative w-full h-full flex items-center justify-center">
  <canvas bind:this={canvas}></canvas>
  <div class="absolute inset-0 flex items-center justify-center flex-col">
    <span class="text-2xl font-bold">{(value * 100).toFixed(0)}%</span>
    {#if label}
      <span class="text-xs text-white/50 mt-0.5">{label}</span>
    {/if}
  </div>
</div>
