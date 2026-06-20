<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { page } from '$app/stores';

  let { value = 0, decimals = 0, prefix = '', suffix = '', duration = 1.5 } = $props();

  let displayValue = $state('0');
  let el: HTMLSpanElement;

  function animate() {
    if (!el) return;
    const obj = { val: 0 };
    gsap.to(obj, {
      val: value,
      duration,
      ease: 'power3.out',
      onUpdate: () => {
        displayValue = prefix + obj.val.toFixed(decimals) + suffix;
      }
    });
  }

  onMount(() => {
    animate();
  });
</script>

<span bind:this={el} class="tabular-nums">{displayValue}</span>
