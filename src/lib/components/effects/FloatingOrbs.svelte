<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';

  interface Props {
    count?: number;
    colors?: string[];
  }

  let { count = 4, colors = ['#4d6cf5', '#f59e0b', '#10b981', '#8b5cf6'] }: Props = $props();

  let container: HTMLDivElement;
  let orbs: HTMLDivElement[] = [];

  onMount(() => {
    if (!container) return;
    const els = container.querySelectorAll('.orb') as NodeListOf<HTMLDivElement>;
    els.forEach((el, i) => {
      const x = 10 + Math.random() * 80;
      const y = 10 + Math.random() * 80;
      const size = 150 + Math.random() * 250;
      el.style.width = size + 'px';
      el.style.height = size + 'px';
      el.style.left = x + '%';
      el.style.top = y + '%';
      gsap.to(el, {
        x: `+=${(Math.random() - 0.5) * 100}`,
        y: `+=${(Math.random() - 0.5) * 100}`,
        scale: 1 + Math.random() * 0.3,
        duration: 6 + Math.random() * 4,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: i * 0.5
      });
      gsap.to(el, {
        opacity: 0.12 + Math.random() * 0.08,
        duration: 4 + Math.random() * 3,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut',
        delay: i * 0.3
      });
    });
  });
</script>

<div bind:this={container} class="fixed inset-0 pointer-events-none overflow-hidden" style="z-index: 0;">
  {#each colors.slice(0, count) as color, i}
    <div
      class="orb absolute rounded-full"
      style="background: radial-gradient(circle, {color}66 0%, {color}00 70%); opacity: 0.08;"
    ></div>
  {/each}
</div>
