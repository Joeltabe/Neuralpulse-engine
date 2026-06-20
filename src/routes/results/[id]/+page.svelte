<script lang="ts">
  import { page } from '$app/stores';
  import { _ } from '$lib/i18n';
  import Card from '$lib/components/ui/Card.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import ScoreCard from '$lib/components/analysis/ScoreCard.svelte';
  import GradeBadge from '$lib/components/analysis/GradeBadge.svelte';
  import RecommendationList from '$lib/components/analysis/RecommendationList.svelte';
  import EngagementCurve from '$lib/components/charts/EngagementCurve.svelte';
  import RadarChart from '$lib/components/charts/RadarChart.svelte';
  import BrainViewer from '$lib/components/brain/BrainViewer.svelte';
  import type { AnalysisResult } from '$lib/types/api';

  let result = $state<AnalysisResult | null>(null);
  let loading = $state(true);
  let brainMode = $state<'attention' | 'dopamine' | 'memory'>('attention');
  let id = $derived($page.params.id);

  async function load() {
    loading = true;
    try {
      const res = await fetch('/api/history/analyses');
      const data = await res.json();
      if (data.success) {
        const found = data.analyses.find((a: any) => a.id === id);
        if (found?.results) result = found.results;
      }
    } catch { /* ignore */ }
    loading = false;
  }

  load();
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <a href="/history" class="text-sm text-white/40 hover:text-white transition-colors">&larr; {$_('common.back')}</a>

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {:else if result}
    <div class="flex items-start gap-6">
      <GradeBadge grade={result.overall_grade} />
      <div>
        <h1 class="text-xl font-bold">{result.filename}</h1>
        <p class="text-sm text-white/50">{result.summary}</p>
      </div>
    </div>
    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <ScoreCard label={$_('common.attention')} value={result.brain_scores.attention.overall} color="#4d6cf5" />
      <ScoreCard label={$_('common.dopamine')} value={result.brain_scores.dopamine.overall} color="#f59e0b" />
      <ScoreCard label={$_('common.memory')} value={result.brain_scores.memory.overall} color="#10b981" />
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card><div class="h-48"><EngagementCurve timestamps={result.timestamp_axis} scores={result.engagement_curve} /></div></Card>
      <Card><div class="h-56"><RadarChart values={[result.brain_scores.attention.overall, result.brain_scores.dopamine.overall, result.brain_scores.memory.overall]} /></div></Card>
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold">{$_('analyze.brain_visualization')}</h3>
          <div class="flex gap-1">
            {#each ['attention', 'dopamine', 'memory'] as mode}
              <button onclick={() => brainMode = mode as 'attention' | 'dopamine' | 'memory'} class={`px-2 py-1 text-xs rounded-lg transition-colors ${brainMode === mode ? 'bg-neural-500/20 text-neural-300' : 'text-white/40'}`}>{mode}</button>
            {/each}
          </div>
        </div>
        <div class="h-56"><BrainViewer roiScores={{...result.brain_scores.attention.roi_breakdown, ...result.brain_scores.dopamine.roi_breakdown, ...result.brain_scores.memory.roi_breakdown}} mode={brainMode} /></div>
      </Card>
      <Card><h3 class="text-sm font-semibold mb-3">{$_('analyze.roi_breakdown')}</h3><RecommendationList recommendations={result.recommendations} /></Card>
    </div>
  {:else}
    <Card class="text-center py-12"><p class="text-white/40">Result not found</p></Card>
  {/if}
</div>
