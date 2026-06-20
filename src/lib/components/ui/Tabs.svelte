<script lang="ts">
  import { gsap } from 'gsap';

  interface Tab {
    value: string;
    label: string;
  }

  interface Props {
    tabs: Tab[];
    active?: string;
    onchange?: (value: string) => void;
    class?: string;
  }

  let { tabs, active = '', onchange, class: className = '' }: Props = $props();

  let indicator: HTMLDivElement;
  let tabRefs: HTMLButtonElement[] = [];

  function select(value: string, idx: number) {
    active = value;
    onchange?.(value);
    if (indicator && tabRefs[idx]) {
      gsap.to(indicator, {
        x: tabRefs[idx].offsetLeft,
        width: tabRefs[idx].offsetWidth,
        duration: 0.3,
        ease: 'power3.out'
      });
    }
  }
</script>

<div class={`relative flex gap-1 p-1 glass rounded-xl ${className}`}>
  <div bind:this={indicator} class="absolute bottom-1 top-1 rounded-lg bg-neural-500/20 transition-none"></div>
  {#each tabs as tab, i}
    <button
      bind:this={tabRefs[i]}
      onclick={() => select(tab.value, i)}
      class={`relative z-10 px-4 py-2 text-sm font-medium rounded-lg transition-colors duration-200 ${active === tab.value ? 'text-white' : 'text-white/50 hover:text-white/80'}`}
    >
      {tab.label}
    </button>
  {/each}
</div>
