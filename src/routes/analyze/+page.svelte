<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { _ } from '$lib/i18n';
  import Button from '$lib/components/ui/Button.svelte';

  const types = [
    { href: '/analyze/video', icon: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664zM21 12a9 9 0 11-18 0 9 9 0 0118 0z', label: 'analyze.video', color: 'neural', ext: 'MP4, MOV, AVI, WebM, MKV' },
    { href: '/analyze/audio', icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z', label: 'analyze.audio', color: 'dopamine', ext: 'MP3, WAV, OGG, M4A, FLAC' },
    { href: '/analyze/text', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', label: 'analyze.text', color: 'memory', ext: 'TXT, MD, HTML or paste directly' }
  ];

  const colorMap: Record<string, string> = { neural: 'from-neural-500/20 to-neural-500/5 border-neural-500/20', dopamine: 'from-dopamine-500/20 to-dopamine-500/5 border-dopamine-500/20', memory: 'from-memory-500/20 to-memory-500/5 border-memory-500/20' };
  const iconColor: Record<string, string> = { neural: 'text-neural-400', dopamine: 'text-dopamine-400', memory: 'text-memory-400' };
  const btnColor = { neural: 'neural', dopamine: 'dopamine', memory: 'memory' } as const;

  onMount(() => {
    gsap.from('.type-card', { opacity: 0, y: 30, duration: 0.6, stagger: 0.15, ease: 'power3.out' });
  });
</script>

<div class="max-w-4xl mx-auto space-y-8">
  <div>
    <h1 class="text-2xl font-bold">{$_('analyze.title')}</h1>
    <p class="text-white/50 mt-1">{$_('analyze.select_type')}</p>
  </div>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
    {#each types as t}
      <a href={t.href} class="type-card glass rounded-2xl p-6 card-hover bg-gradient-to-br {colorMap[t.color]} flex flex-col items-center text-center gap-4">
        <div class="w-16 h-16 rounded-2xl bg-white/5 flex items-center justify-center">
          <svg class="w-8 h-8 {iconColor[t.color]}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={t.icon}/></svg>
        </div>
        <div>
          <h3 class="text-lg font-semibold">{$_(t.label)}</h3>
          <p class="text-xs text-white/40 mt-1">{t.ext}</p>
        </div>
        <span class="text-xs text-neural-400 font-medium">50 tokens &rarr;</span>
      </a>
    {/each}
  </div>
</div>
