<script lang="ts">
  import { onMount } from 'svelte';
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import Tabs from '$lib/components/ui/Tabs.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import { goto } from '$app/navigation';

  let activeTab = $state('analyses');
  let analyses: any[] = $state([]);
  let stats: any = $state(null);
  let loading = $state(true);

  const tabs = [
    { value: 'analyses', label: 'Analyses' },
    { value: 'stats', label: 'Stats' }
  ];

  onMount(async () => {
    try {
      const [aRes, sRes] = await Promise.all([
        fetch('/api/history/analyses'),
        fetch('/api/history/stats')
      ]);
      const aData = await aRes.json();
      const sData = await sRes.json();
      if (aData.success) analyses = aData.analyses || [];
      if (sData.success) stats = sData.stats || sData;
    } catch { /* ignore */ }
    loading = false;
  });
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <h1 class="text-2xl font-bold">{$_('history.title')}</h1>

  <Tabs {tabs} onchange={(v) => activeTab = v} />

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {:else if activeTab === 'analyses'}
    {#if analyses.length === 0}
      <Card class="text-center py-12"><p class="text-white/40">No analyses yet</p></Card>
    {:else}
      <div class="space-y-2">
        {#each analyses as item}
          <button onclick={() => goto(`/results/${item.id}`)} class="w-full text-left glass rounded-xl p-4 hover:border-neural-500/30 transition-all">
            <div class="flex items-center justify-between">
              <div class="min-w-0 flex-1">
                <p class="text-sm font-medium truncate">{item.filename || item.media_type || 'Analysis'}</p>
                <p class="text-xs text-white/40 mt-0.5">{item.media_type} &middot; {new Date(item.created_at || item.timestamp).toLocaleDateString()}</p>
              </div>
              <div class="flex items-center gap-3 ml-3">
                {#if item.results?.overall_grade}
                  <Badge>{item.results.overall_grade}</Badge>
                {/if}
                <span class="text-xs text-white/30">&rarr;</span>
              </div>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  {:else}
    {#if stats}
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card class="text-center"><p class="text-2xl font-bold gradient-text">{stats.total_tokens || 0}</p><p class="text-xs text-white/40 mt-1">Total Tokens</p></Card>
        <Card class="text-center"><p class="text-2xl font-bold gradient-text">{stats.total_analyses || 0}</p><p class="text-xs text-white/40 mt-1">Analyses</p></Card>
        <Card class="text-center"><p class="text-2xl font-bold gradient-text">{stats.video_count || 0}</p><p class="text-xs text-white/40 mt-1">Videos</p></Card>
        <Card class="text-center"><p class="text-2xl font-bold gradient-text">{stats.average_score ? `${(stats.average_score*100).toFixed(0)}%` : '—'}</p><p class="text-xs text-white/40 mt-1">Avg Score</p></Card>
      </div>
    {:else}
      <Card class="text-center py-12"><p class="text-white/40">No stats available</p></Card>
    {/if}
  {/if}
</div>
