<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  interface Props {
    labels?: string[];
    values?: number[];
    color?: string;
  }

  let { labels = ['Attention', 'Dopamine', 'Memory'], values = [0, 0, 0], color = '#4d6cf5' }: Props = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart;

  onMount(() => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const plainLabels = [...labels];
    const plainValues = [...values];

    chart = new Chart(ctx, {
      type: 'radar',
      data: {
        labels: plainLabels,
        datasets: [{
          data: plainValues,
          borderColor: color,
          backgroundColor: color + '30',
          borderWidth: 2,
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 4
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 800, easing: 'easeOutQuart' },
        plugins: { legend: { display: false } },
        scales: {
          r: {
            min: 0, max: 1,
            grid: { color: 'rgba(255,255,255,0.08)' },
            angleLines: { color: 'rgba(255,255,255,0.08)' },
            pointLabels: { color: 'rgba(255,255,255,0.6)', font: { size: 11 } },
            ticks: { display: false }
          }
        }
      }
    });
  });

  onDestroy(() => chart?.destroy());
</script>

<div class="w-full h-full">
  <canvas bind:this={canvas}></canvas>
</div>
