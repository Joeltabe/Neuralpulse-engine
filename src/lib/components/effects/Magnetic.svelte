<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';

  interface Props {
    children?: import('svelte').Snippet;
    strength?: number;
    radius?: number;
  }

  let { children, strength = 0.3, radius = 150 }: Props = $props();

  let el: HTMLDivElement;

  function move(e: MouseEvent) {
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const dx = (e.clientX - cx) / radius;
    const dy = (e.clientY - cy) / radius;
    const dist = Math.sqrt(dx * dx + dy * dy);
    if (dist > 1) return;
    gsap.to(el, {
      x: dx * radius * strength,
      y: dy * radius * strength,
      duration: 0.4,
      ease: 'power2.out'
    });
  }

  function reset() {
    if (!el) return;
    gsap.to(el, { x: 0, y: 0, duration: 0.6, ease: 'elastic.out(1, 0.4)' });
  }

  onMount(() => {
    if (!el) return;
    el.addEventListener('mousemove', move);
    el.addEventListener('mouseleave', reset);
    return () => { el?.removeEventListener('mousemove', move); el?.removeEventListener('mouseleave', reset); };
  });
</script>

<div bind:this={el} class="inline-block" style="will-change: transform;">
  {@render children?.()}
</div>
