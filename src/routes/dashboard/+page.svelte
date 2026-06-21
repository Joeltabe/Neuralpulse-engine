<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { page } from '$app/stores';
  import { _ } from '$lib/i18n';
  import Badge from '$lib/components/ui/Badge.svelte';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import AnimatedCounter from '$lib/components/effects/AnimatedCounter.svelte';
  import Reveal from '$lib/components/effects/Reveal.svelte';
  import Magnetic from '$lib/components/effects/Magnetic.svelte';
  import { formatRelativeTime, gradeColor } from '$lib/utils/formatters';
  import type { AnalysisHistoryItem } from '$lib/types/api';

  let recentAnalyses = $state<AnalysisHistoryItem[]>([]);
  let loading = $state(true);
  let stats = $state({ total: 0, tokens: 0, by_type: {} as Record<string, number>, avg_grade: '' });

  let user = $derived($page.data.user);

  const quickActions = [
    { href: '/analyze/video', label: 'dashboard.upload_video', icon: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664zM21 12a9 9 0 11-18 0 9 9 0 0118 0z', bgClass: 'bg-neural-500/10', textClass: 'text-neural-400' },
    { href: '/analyze/audio', label: 'dashboard.upload_audio', icon: 'M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z', bgClass: 'bg-dopamine-500/10', textClass: 'text-dopamine-400' },
    { href: '/analyze/text', label: 'dashboard.analyze_text', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', bgClass: 'bg-memory-500/10', textClass: 'text-memory-400' }
  ];

  onMount(async () => {
    try {
      const [aRes, sRes] = await Promise.all([
        fetch('/api/history/analyses'),
        fetch('/api/history/stats')
      ]);
      const aData = await aRes.json();
      const sData = await sRes.json();
      if (aData.success) recentAnalyses = aData.analyses || [];
      if (sData.success && sData.analyses?.length) {
        const s = sData.analyses[0];
        stats = { total: s.total_analyses || 0, tokens: s.total_tokens_used || 0, by_type: s.by_type || {}, avg_grade: s.avg_grade || '' };
      }
    } catch { /* ignore */ }
    loading = false;

    gsap.to('.dash-header', { opacity: 1, y: 0, duration: 0.6, ease: 'power3.out' });
    gsap.to('.quick-action', {
      opacity: 1, y: 0, scale: 1, duration: 0.5, stagger: 0.12, ease: 'back.out(1.4)',
      delay: 0.2
    });
    gsap.to('.stat-card', {
      opacity: 1, y: 0, duration: 0.6, stagger: 0.1, ease: 'power3.out',
      delay: 0.3
    });
  });
</script>

<div class="max-w-7xl mx-auto space-y-8">
  <div class="dash-header flex flex-col md:flex-row md:items-center justify-between gap-4 opacity-0 -translate-y-5">
    <div>
      <h1 class="text-2xl font-bold">{$_('dashboard.title')}</h1>
      <p class="text-white/50 mt-1">{$_('dashboard.welcome')}, {user?.name || 'Creator'}.</p>
    </div>
    <div class="flex gap-3">
      <Magnetic strength={0.15} radius={100}>
        <Button href="/analyze" variant="gradient" size="md">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"/></svg>
          New Analysis
        </Button>
      </Magnetic>
    </div>
  </div>

  <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
    {#each quickActions as item}
      <a href={item.href} class="quick-action glass rounded-2xl p-5 card-hover flex items-center gap-4 group opacity-0 translate-y-[30px] scale-[0.95]">
        <div class="w-10 h-10 rounded-xl {item.bgClass} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-300">
          <svg class="w-5 h-5 {item.textClass}" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={item.icon}/></svg>
        </div>
        <span class="text-sm font-medium">{$_(item.label)}</span>
      </a>
    {/each}
  </div>

  <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
    <Card class="stat-card opacity-0 translate-y-[40px]">
      <p class="text-xs text-white/40 uppercase tracking-wider">{$_('dashboard.total_analyses')}</p>
      <p class="text-3xl font-bold mt-2 gradient-text"><AnimatedCounter value={stats.total || 0} /></p>
    </Card>
    <Card class="stat-card opacity-0 translate-y-[40px]">
      <p class="text-xs text-white/40 uppercase tracking-wider">{$_('dashboard.tokens_used')}</p>
      <p class="text-3xl font-bold mt-2 text-dopamine-400"><AnimatedCounter value={stats.tokens || 0} /></p>
    </Card>
    <Card class="stat-card opacity-0 translate-y-[40px]">
      <p class="text-xs text-white/40 uppercase tracking-wider">{$_('dashboard.avg_grade')}</p>
      <p class="text-3xl font-bold mt-2 {gradeColor(stats.avg_grade)}">{stats.avg_grade || '—'}</p>
    </Card>
    <Card class="stat-card opacity-0 translate-y-[40px]">
      <p class="text-xs text-white/40 uppercase tracking-wider">{$_('common.token_balance')}</p>
      <p class="text-3xl font-bold mt-2 text-dopamine-400"><AnimatedCounter value={user?.token_balance || 0} /></p>
    </Card>
  </div>

  <Reveal>
    <div>
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold">{$_('dashboard.recent_analyses')}</h2>
        <a href="/history" class="text-sm text-neural-400 hover:text-neural-300 transition-colors">{$_('dashboard.view_all')} &rarr;</a>
      </div>
      {#if loading}
        <div class="flex justify-center py-12"><Spinner size="lg" /></div>
      {:else if recentAnalyses.length === 0}
        <Card class="text-center py-12">
          <p class="text-white/40">{$_('dashboard.no_analyses_yet')}</p>
          <Magnetic strength={0.15} radius={100}>
            <Button href="/analyze" variant="primary" size="sm" class="mt-4">Start Analyzing</Button>
          </Magnetic>
        </Card>
      {:else}
        <div class="space-y-2">
          {#each recentAnalyses.slice(0, 5) as item, i}
            <a
              href="/results/{item.id}"
              class="glass rounded-xl p-4 flex items-center justify-between card-hover group"
              style="animation: slide-in 0.4s {i * 0.08}s ease-out both;"
            >
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <Badge variant={item.media_type as 'attention' | 'dopamine' | 'memory'}>{item.media_type}</Badge>
                  <span class="text-sm font-medium truncate">{item.filename}</span>
                </div>
                <p class="text-xs text-white/40 mt-1">{formatRelativeTime(item.created_at)}</p>
              </div>
              <div class="flex items-center gap-4 shrink-0">
                <div class="text-right">
                  <span class="text-xs text-white/40">{$_('common.grade')}</span>
                  <p class={`text-sm font-bold ${gradeColor(item.overall_grade)}`}>{item.overall_grade}</p>
                </div>
                <svg class="w-4 h-4 text-white/30 group-hover:text-white/60 transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
              </div>
            </a>
          {/each}
        </div>
      {/if}
    </div>
  </Reveal>
</div>

<style>
  @keyframes slide-in {
    from { opacity: 0; transform: translateX(-20px); }
    to { opacity: 1; transform: translateX(0); }
  }
</style>
