<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Chart from 'chart.js/auto';

  interface Props {
    timestamps?: number[];
    scores?: number[];
    label?: string;
    color?: string;
  }

  let { timestamps = [], scores = [], label = 'Engagement', color = '#4d6cf5' }: Props = $props();

  let canvas: HTMLCanvasElement;
  let chart: Chart;

  onMount(() => {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const plainLabels = [...timestamps].map(t => `${t.toFixed(1)}s`);
    const plainScores = [...scores];

    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: plainLabels,
        datasets: [{
          label,
          data: plainScores,
          borderColor: color,
          backgroundColor: color + '20',
          fill: true,
          tension: 0.4,
          pointRadius: 0,
          pointHitRadius: 10,
          borderWidth: 2
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 800, easing: 'easeOutQuart' },
        plugins: { legend: { display: false } },
        scales: {
          x: {
            display: true,
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: 'rgba(255,255,255,0.4)', font: { size: 10 }, maxTicksLimit: 10 }
          },
          y: {
            min: 0, max: 1,
            grid: { color: 'rgba(255,255,255,0.05)' },
            ticks: { color: 'rgba(255,255,255,0.4)', font: { size: 10 }, callback: (v) => `${(Number(v) * 100).toFixed(0)}%` }
          }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  });

  onDestroy(() => chart?.destroy());
</script>

<div class="w-full h-full">
  <canvas bind:this={canvas}></canvas>
</div>
