<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { ScrollTrigger } from 'gsap/ScrollTrigger';

  interface Props {
    children?: import('svelte').Snippet;
    type?: 'fade-up' | 'fade-left' | 'fade-right' | 'scale-in' | 'flip-up';
    delay?: number;
    duration?: number;
    distance?: number;
    stagger?: number;
    threshold?: number;
  }

  let { children, type = 'fade-up', delay = 0, duration = 0.8, distance = 50, stagger = 0, threshold = 0.15 }: Props = $props();

  let el: HTMLDivElement;

  onMount(() => {
    if (!el) return;
    gsap.registerPlugin(ScrollTrigger);
    const vars: gsap.TweenVars = { opacity: 0 };
    if (type === 'fade-up') { vars.y = distance; }
    else if (type === 'fade-left') { vars.x = -distance; }
    else if (type === 'fade-right') { vars.x = distance; }
    else if (type === 'scale-in') { vars.scale = 0.8; }
    else if (type === 'flip-up') { vars.rotationX = 90; vars.y = distance; }

    gsap.set(el, vars);
    if (stagger > 0) {
      const children = el.querySelectorAll('.reveal-item');
      gsap.fromTo(children,
        { opacity: 0, y: distance },
        {
          opacity: 1, y: 0, duration, delay,
          stagger,
          ease: 'power3.out',
          scrollTrigger: { trigger: el, start: `top ${(1 - threshold) * 100}%` }
        }
      );
    } else {
      gsap.to(el, {
        opacity: 1, y: 0, x: 0, scale: 1, rotationX: 0,
        duration, delay,
        ease: 'power3.out',
        scrollTrigger: { trigger: el, start: `top ${(1 - threshold) * 100}%` }
      });
    }
  });
</script>

<div bind:this={el} class="contents">
  {@render children?.()}
</div>
