<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { ScrollTrigger } from 'gsap/ScrollTrigger';
  import Button from '$lib/components/ui/Button.svelte';
  import FloatingOrbs from '$lib/components/effects/FloatingOrbs.svelte';
  import Magnetic from '$lib/components/effects/Magnetic.svelte';
  import TiltCard from '$lib/components/effects/TiltCard.svelte';
  import TextReveal from '$lib/components/effects/TextReveal.svelte';
  import Reveal from '$lib/components/effects/Reveal.svelte';
  import { _ } from '$lib/i18n';

  let heroEl: HTMLDivElement;
  let statsEl: HTMLElement;
  let videoEls: HTMLVideoElement[] = [];
  let activeVideo = $state(0);

  const videos = [
    { src: '/brain/253879_medium.mp4', label: 'brain' },
    { src: '/brain/143567-782758325_medium.mp4', label: 'neurons' },
    { src: '/brain/159049-818026306_medium.mp4', label: 'network' },
  ];

  function nextVideo() {
    activeVideo = (activeVideo + 1) % videos.length;
  }

  onMount(() => {
    gsap.registerPlugin(ScrollTrigger);

    const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });
    tl.from('.badge-pill', { opacity: 0, y: -20, scale: 0.8, duration: 0.6 })
      .from('.hero-title-line', { opacity: 0, x: -80, duration: 0.8, stagger: 0.15 }, '-=0.3')
      .from('.hero-sub', { opacity: 0, y: 30, duration: 0.8 }, '-=0.5')
      .from('.hero-cta > *', { opacity: 0, y: 20, duration: 0.5, stagger: 0.15 }, '-=0.3')
      .from('.hero-glow-1', { opacity: 0, scale: 0, duration: 0.8 }, '-=0.5');

    if (videoEls[0]) {
      videoEls[0].play();
    }
  });

  $effect(() => {
    const idx = activeVideo;
    if (videoEls[idx]) {
      videoEls[idx].play();
    }
  });

  onMount(() => {
    gsap.utils.toArray<HTMLElement>('[data-morph]').forEach((el) => {
      gsap.to(el, {
        y: () => gsap.utils.random(-8, 8),
        x: () => gsap.utils.random(-6, 6),
        duration: 2 + Math.random() * 2,
        repeat: -1,
        yoyo: true,
        ease: 'sine.inOut'
      });
    });

    gsap.from('.stat-number', {
      scrollTrigger: { trigger: '.stats-section', start: 'top 80%' },
      textContent: 0,
      duration: 2,
      ease: 'power2.out',
      snap: { textContent: 1 },
      stagger: 0.2
    });

    if (statsEl) {
      gsap.from(statsEl.querySelectorAll('.stat-item'), {
        scrollTrigger: { trigger: statsEl, start: 'top 80%' },
        opacity: 0, y: 40, scale: 0.9,
        duration: 0.6,
        stagger: 0.15,
        ease: 'back.out(1.4)'
      });
    }
  });

  const features = [
    { icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z', key: 'feature_attention', color: '#4d6cf5' },
    { icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z', key: 'feature_dopamine', color: '#f59e0b' },
    { icon: 'M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10', key: 'feature_memory', color: '#10b981' },
    { icon: 'M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2', key: 'feature_ab', color: '#8b5cf6' },
    { icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z', key: 'feature_copy', color: '#ec4899' },
    { icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z', key: 'feature_thumbnail', color: '#06b6d4' }
  ];
</script>

<FloatingOrbs count={5} colors={['#4d6cf5', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899']} />

<div class="relative z-10">
  <!-- Nav -->
  <nav class="flex items-center justify-between px-6 py-4 max-w-7xl mx-auto relative z-20">
    <div class="flex items-center gap-3">
      <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-neural-500 to-dopamine-500 flex items-center justify-center" data-morph>
        <svg class="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"/></svg>
      </div>
      <span class="font-bold text-lg gradient-text">NeuralPulse</span>
    </div>
    <div class="flex items-center gap-3">
      <a href="/login" class="text-sm text-white/60 hover:text-white transition-colors px-3 py-2">Sign In</a>
      <Magnetic strength={0.15} radius={100}>
        <Button href="/register" variant="primary" size="sm">Get Started</Button>
      </Magnetic>
    </div>
  </nav>

  <!-- Hero -->
  <section class="max-w-7xl mx-auto px-6 pt-16 pb-32 flex flex-col lg:flex-row items-center gap-16 relative">
    <div class="hero-glow-1 absolute -top-20 -left-20 w-96 h-96 rounded-full bg-neural-500/5 blur-[120px] pointer-events-none"></div>
    <div class="flex-1 text-center lg:text-left relative z-10">
      <div class="badge-pill inline-flex items-center gap-2 px-3 py-1 rounded-full bg-neural-500/10 border border-neural-500/20 text-neural-400 text-xs font-medium mb-6">
        <span class="w-1.5 h-1.5 rounded-full bg-neural-400 animate-pulse"></span>
        v1.0 — Neuromarketing SaaS
      </div>
      <h1 class="hero-title text-4xl md:text-6xl lg:text-7xl font-black leading-tight text-balance" bind:this={heroEl}>
        <span class="hero-title-line block">See Inside Your</span>
        <span class="hero-title-line block gradient-text">Audience's Brain</span>
      </h1>
      <p class="hero-sub text-lg md:text-xl text-white/50 mt-6 max-w-xl leading-relaxed">
        {$_('landing.hero_subtitle')}
      </p>
      <div class="hero-cta flex flex-col sm:flex-row items-center gap-4 mt-8">
        <Magnetic strength={0.2} radius={120}>
          <Button href="/register" variant="gradient" size="lg">{$_('landing.cta_start')}</Button>
        </Magnetic>
        <Magnetic strength={0.1} radius={80}>
          <a href="/login?demo=true" class="text-sm text-white/50 hover:text-white transition-colors px-4 py-2 group">
            {$_('landing.cta_demo')} <span class="inline-block group-hover:translate-x-1 transition-transform">&rarr;</span>
          </a>
        </Magnetic>
      </div>
    </div>
    <div class="flex-1 flex justify-center relative">
      <div class="relative w-72 h-72 md:w-96 md:h-96">
        <!-- Glow layers on top of video -->
        <div class="absolute inset-0 rounded-full bg-gradient-to-br from-neural-500/20 via-dopamine-500/10 to-memory-500/20 animate-pulse-slow blur-3xl z-10 pointer-events-none"></div>
        <div class="absolute inset-4 rounded-full bg-gradient-to-br from-neural-500/30 via-dopamine-500/20 to-memory-500/30 animate-float blur-2xl z-10 pointer-events-none"></div>

        <!-- Video carousel -->
        <div class="absolute inset-0 rounded-full overflow-hidden z-0 ring-1 ring-white/5">
          <div class="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-transparent z-[1] pointer-events-none"></div>
          {#each videos as v, i}
            <video
              class="absolute inset-0 w-full h-full object-cover transition-opacity duration-1000"
              class:opacity-100={activeVideo === i}
              class:opacity-0={activeVideo !== i}
              src={v.src}
              muted
              playsinline
              preload="metadata"
              bind:this={videoEls[i]}
              onended={nextVideo}
              style="pointer-events: none;"
            ></video>
          {/each}
        </div>

        {#each [0, 1, 2] as i}
          <div
            class="absolute inset-0 rounded-full border border-neural-500/10 z-20 pointer-events-none"
            style="animation: ripple-expand 3s {i * 0.8}s ease-out infinite;"
          ></div>
        {/each}
      </div>
    </div>
  </section>

  <!-- Features -->
  <section class="max-w-7xl mx-auto px-6 py-24">
    <Reveal>
      <div class="text-center mb-16">
        <h2 class="text-3xl md:text-4xl font-bold">Why <span class="gradient-text">NeuralPulse</span>?</h2>
        <p class="text-white/50 mt-4 max-w-2xl mx-auto">Six core capabilities powered by simulated fMRI brain activity</p>
      </div>
    </Reveal>
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {#each features as feat, i}
        <Reveal type="fade-up" delay={i * 0.1}>
          <TiltCard maxTilt={8} scale={1.01} glare={true}>
            <div class="glass rounded-2xl p-6 card-hover relative overflow-hidden group" style="border-color: {feat.color}22;">
              <div class="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500" style="background: radial-gradient(600px circle at var(--mx, 50%) var(--my, 50%), {feat.color}08 0%, transparent 60%);"></div>
              <div class="w-10 h-10 rounded-xl flex items-center justify-center mb-4 relative" style="background: {feat.color}15;">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color: {feat.color};"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={feat.icon}/></svg>
              </div>
              <h3 class="text-lg font-semibold mb-2 relative">{$_(`landing.${feat.key}`)}</h3>
              <p class="text-sm text-white/50 leading-relaxed relative">{$_(`landing.${feat.key}_desc`)}</p>
            </div>
          </TiltCard>
        </Reveal>
      {/each}
    </div>
  </section>

  <!-- Stats -->
  <section class="max-w-7xl mx-auto px-6 py-24" bind:this={statsEl}>
    <Reveal>
      <div class="stats-section glass rounded-3xl p-8 md:p-12 relative overflow-hidden">
        <div class="absolute inset-0 bg-gradient-to-br from-neural-500/5 via-dopamine-500/5 to-memory-500/5"></div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-8 text-center relative">
          <div class="stat-item">
            <p class="text-5xl font-black gradient-text"><span class="stat-number" data-target="10000">0</span>+</p>
            <p class="text-sm text-white/50 mt-2">{$_('landing.stats_analyzed')}</p>
          </div>
          <div class="stat-item">
            <p class="text-5xl font-black gradient-text"><span class="stat-number" data-target="70000">0</span></p>
            <p class="text-sm text-white/50 mt-2">{$_('landing.stats_neurons')}</p>
          </div>
          <div class="stat-item">
            <p class="text-5xl font-black gradient-text"><span class="stat-number" data-target="94">0</span>%</p>
            <p class="text-sm text-white/50 mt-2">{$_('landing.stats_accuracy')}</p>
          </div>
        </div>
      </div>
    </Reveal>
  </section>

  <!-- CTA -->
  <section class="max-w-7xl mx-auto px-6 py-24 text-center">
    <Reveal type="scale-in">
      <h2 class="text-3xl md:text-4xl font-bold mb-4">Ready to optimize your ads with brain science?</h2>
      <p class="text-white/50 mb-8 max-w-xl mx-auto">Start analyzing your content with simulated fMRI responses. No hardware required.</p>
      <Magnetic strength={0.25} radius={140}>
        <Button href="/register" variant="gradient" size="xl">Start Analyzing Free</Button>
      </Magnetic>
    </Reveal>
  </section>

  <!-- Footer -->
  <footer class="border-t border-white/5 py-8 px-6 text-center text-sm text-white/30">
    <p>&copy; {new Date().getFullYear()} NeuralPulse Engine. All rights reserved.</p>
  </footer>
</div>

<style>
  @keyframes ripple-expand {
    0% { transform: scale(0.8); opacity: 0.4; }
    100% { transform: scale(1.4); opacity: 0; }
  }
</style>
