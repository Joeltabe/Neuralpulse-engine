<script lang="ts">
  import { _ } from '$lib/i18n';
  import { error as showError } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import FileUpload from '$lib/components/ui/FileUpload.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import ScoreCard from '$lib/components/analysis/ScoreCard.svelte';
  import GradeBadge from '$lib/components/analysis/GradeBadge.svelte';
  import RecommendationList from '$lib/components/analysis/RecommendationList.svelte';
  import EngagementCurve from '$lib/components/charts/EngagementCurve.svelte';
  import type { AnalysisResult } from '$lib/types/api';

  let file = $state<File | null>(null);
  let loading = $state(false);
  let result = $state<AnalysisResult | null>(null);

  const exts = ['.mp3', '.wav', '.ogg', '.m4a', '.flac'];

  function handleUpload(f: File | File[]) {
    const fileObj = Array.isArray(f) ? f[0] : f;
    const ext = '.' + fileObj.name.split('.').pop()?.toLowerCase();
    if (!exts.includes(ext)) { showError($_('errors.invalid_file')); return; }
    file = fileObj;
  }

  async function analyze() {
    if (!file) return;
    loading = true;
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/analyze/audio', { method: 'POST', body: form });
      const data = await res.json();
      if (data.success && data.data) result = data.data;
      else showError(data.error || $_('errors.analysis_failed'));
    } catch { showError($_('errors.network')); }
    finally { loading = false; }
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">{$_('analyze.audio')}</h1>
    <p class="text-sm text-white/50 mt-1">{$_('analyze.tokens_cost', { tokens: 30 })}</p>
  </div>

  {#if !result}
    <Card>
      <div class="space-y-4">
        <FileUpload accept=".mp3,.wav,.ogg,.m4a,.flac" label={$_('analyze.drop_audio')} onupload={handleUpload} />
        {#if file}
          <div class="glass rounded-xl p-3 flex items-center justify-between">
            <span class="text-sm truncate">{file.name}</span>
            <span class="text-xs text-white/40">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
          </div>
        {/if}
        <Button onclick={analyze} variant="gradient" size="lg" class="w-full" disabled={!file} loading={loading} />
      </div>
    </Card>
    <div class="flex gap-3 justify-center">
      <a href="/analyze/video" class="glass rounded-xl px-4 py-2 text-sm text-white/50 hover:text-white hover:bg-white/5 transition-colors">Video Analysis</a>
      <a href="/analyze/text" class="glass rounded-xl px-4 py-2 text-sm text-white/50 hover:text-white hover:bg-white/5 transition-colors">Text Analysis</a>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {/if}

  {#if result}
    <div class="space-y-6">
      <div class="flex items-start gap-6">
        <GradeBadge grade={result.overall_grade} />
        <div>
          <h2 class="text-xl font-bold">{result.filename}</h2>
          <p class="text-sm text-white/50">{result.summary}</p>
        </div>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <ScoreCard label={$_('common.attention')} value={result.brain_scores.attention.overall} color="#4d6cf5" />
        <ScoreCard label={$_('common.dopamine')} value={result.brain_scores.dopamine.overall} color="#f59e0b" />
        <ScoreCard label={$_('common.memory')} value={result.brain_scores.memory.overall} color="#10b981" />
      </div>
      <Card>
        <h3 class="text-sm font-semibold mb-3">{$_('analyze.engagement_curve')}</h3>
        <div class="h-48"><EngagementCurve timestamps={result.timestamp_axis} scores={result.engagement_curve} /></div>
      </Card>
      {#if result.recommendations?.length}
        <Card>
          <h3 class="text-sm font-semibold mb-3">{$_('analyze.recommendations')}</h3>
          <RecommendationList recommendations={result.recommendations} />
        </Card>
      {/if}
      <div class="flex justify-center">
        <Button onclick={() => { result = null; file = null; }} variant="secondary">Analyze Another Audio</Button>
      </div>
    </div>
  {/if}
</div>
