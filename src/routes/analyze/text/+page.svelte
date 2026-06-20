<script lang="ts">
  import { _ } from '$lib/i18n';
  import { error as showError } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import ScoreCard from '$lib/components/analysis/ScoreCard.svelte';
  import GradeBadge from '$lib/components/analysis/GradeBadge.svelte';
  import RecommendationList from '$lib/components/analysis/RecommendationList.svelte';
  import RoiBreakdown from '$lib/components/analysis/RoiBreakdown.svelte';
  import type { AnalysisResult } from '$lib/types/api';

  let text = $state('');
  let loading = $state(false);
  let result = $state<AnalysisResult | null>(null);

  async function analyze() {
    if (!text.trim()) return;
    loading = true;
    try {
      const res = await fetch('/api/analyze/text', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, filename: 'text_analysis' })
      });
      const data = await res.json();
      if (data.success && data.data) result = data.data;
      else showError(data.error || $_('errors.analysis_failed'));
    } catch { showError($_('errors.network')); }
    finally { loading = false; }
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">{$_('analyze.text')}</h1>
    <p class="text-sm text-white/50 mt-1">{$_('analyze.tokens_cost', { tokens: 10 })}</p>
  </div>

  {#if !result}
    <Card>
      <div class="space-y-4">
        <Input type="textarea" placeholder={$_('analyze.paste_text')} bind:value={text} />
        <Button onclick={analyze} variant="gradient" size="lg" class="w-full" disabled={!text.trim()} loading={loading}>
          {loading ? $_('analyze.analyzing') : 'Analyze Text →'}
        </Button>
      </div>
    </Card>
  {/if}

  {#if loading}<div class="flex justify-center py-16"><Spinner size="lg" /></div>{/if}

  {#if result}
    <div class="space-y-6">
      <div class="flex items-start gap-6">
        <GradeBadge grade={result.overall_grade} />
        <div><h2 class="text-xl font-bold">{$_('analyze.results_title')}</h2><p class="text-sm text-white/50">{result.summary}</p></div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <ScoreCard label={$_('common.attention')} value={result.brain_scores.attention.overall} color="#4d6cf5" />
        <ScoreCard label={$_('common.dopamine')} value={result.brain_scores.dopamine.overall} color="#f59e0b" />
        <ScoreCard label={$_('common.memory')} value={result.brain_scores.memory.overall} color="#10b981" />
      </div>
      <Card>
        <h3 class="text-sm font-semibold mb-3">{$_('analyze.roi_breakdown')}</h3>
        <div class="grid grid-cols-3 gap-4">
          <RoiBreakdown roi_breakdown={result.brain_scores.attention.roi_breakdown} color="#4d6cf5" />
          <RoiBreakdown roi_breakdown={result.brain_scores.dopamine.roi_breakdown} color="#f59e0b" />
          <RoiBreakdown roi_breakdown={result.brain_scores.memory.roi_breakdown} color="#10b981" />
        </div>
      </Card>
      {#if result.recommendations?.length}
        <Card><h3 class="text-sm font-semibold mb-3">{$_('analyze.recommendations')}</h3><RecommendationList recommendations={result.recommendations} /></Card>
      {/if}
      <div class="flex justify-center">
        <Button onclick={() => { result = null; text = ''; }} variant="secondary">Analyze Another Text</Button>
      </div>
    </div>
  {/if}
</div>
