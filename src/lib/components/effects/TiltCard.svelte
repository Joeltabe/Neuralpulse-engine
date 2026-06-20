<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';

  interface Props {
    children?: import('svelte').Snippet;
    maxTilt?: number;
    glare?: boolean;
    scale?: number;
    class?: string;
  }

  let { children, maxTilt = 10, glare = true, scale = 1.02, class: className = '' }: Props = $props();

  let el: HTMLDivElement;
  let glareEl = $state<HTMLDivElement | null>(null);

  function move(e: MouseEvent) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / (rect.width / 2);
    const dy = (e.clientY - cy) / (rect.height / 2);
    const rx = -dy * maxTilt;
    const ry = dx * maxTilt;
    gsap.to(el, {
      rotateX: rx,
      rotateY: ry,
      scale,
      duration: 0.3,
      ease: 'power2.out'
    });
    if (glare && glareEl) {
      const glareX = dx * 50 + 50;
      const glareY = dy * 50 + 50;
      gsap.to(glareEl, {
        background: `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,0.1) 0%, transparent 60%)`,
        duration: 0.3,
        ease: 'power2.out'
      });
    }
  }

  function reset() {
    if (!el) return;
    gsap.to(el, {
      rotateX: 0, rotateY: 0, scale: 1,
      duration: 0.5,
      ease: 'elastic.out(1, 0.4)'
    });
    if (glare && glareEl) {
      gsap.to(glareEl, { background: 'transparent', duration: 0.5 });
    }
  }

  onMount(() => {
    if (!el) return;
    el.addEventListener('mousemove', move);
    el.addEventListener('mouseleave', reset);
    return () => { el?.removeEventListener('mousemove', move); el?.removeEventListener('mouseleave', reset); };
  });
</script>

<div
  bind:this={el}
  class="relative perspective-1000 {className}"
  style="transform-style: preserve-3d; will-change: transform;"
>
  {#if glare}
    <div bind:this={glareEl} class="absolute inset-0 rounded-2xl pointer-events-none z-10" style="mix-blend-mode: overlay;"></div>
  {/if}
  <div style="transform-style: preserve-3d;">
    {@render children?.()}
  </div>
</div>
