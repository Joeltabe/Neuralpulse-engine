<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { _ } from '$lib/i18n';
  import { error as showError } from '$lib/stores/notifications';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import FileUpload from '$lib/components/ui/FileUpload.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import ScoreCard from '$lib/components/analysis/ScoreCard.svelte';
  import GradeBadge from '$lib/components/analysis/GradeBadge.svelte';
  import RecommendationList from '$lib/components/analysis/RecommendationList.svelte';
  import RoiBreakdown from '$lib/components/analysis/RoiBreakdown.svelte';
  import EngagementCurve from '$lib/components/charts/EngagementCurve.svelte';
  import RadarChart from '$lib/components/charts/RadarChart.svelte';
  import BrainViewer from '$lib/components/brain/BrainViewer.svelte';
  import type { AnalysisResult } from '$lib/types/api';

  let file = $state<File | null>(null);
  let loading = $state(false);
  let result = $state<AnalysisResult | null>(null);
  let brainMode = $state<'attention' | 'dopamine' | 'memory'>('attention');

  const videoExts = ['.mp4', '.mov', '.avi', '.webm', '.mkv'];

  function handleUpload(f: File | File[]) {
    const fileObj = Array.isArray(f) ? f[0] : f;
    const ext = '.' + fileObj.name.split('.').pop()?.toLowerCase();
    if (!videoExts.includes(ext)) { showError($_('errors.invalid_file')); return; }
    file = fileObj;
  }

  async function analyze() {
    if (!file) return;
    loading = true;
    try {
      const form = new FormData();
      form.append('file', file);
      const res = await fetch('/api/analyze/video', { method: 'POST', body: form });
      const data = await res.json();
      if (data.success && data.data) {
        result = data.data;
        gsap.from('.result-section', { opacity: 0, y: 20, duration: 0.5, stagger: 0.1, ease: 'power3.out' });
      } else {
        showError(data.error || $_('errors.analysis_failed'));
      }
    } catch { showError($_('errors.network')); }
    finally { loading = false; }
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <div>
    <h1 class="text-2xl font-bold">{$_('analyze.video')}</h1>
    <p class="text-sm text-white/50 mt-1">{$_('analyze.tokens_cost', { tokens: 50 })}</p>
  </div>

  {#if !result}
    <Card>
      <div class="space-y-4">
        <FileUpload accept=".mp4,.mov,.avi,.webm,.mkv" label={$_('analyze.drop_video')} onupload={handleUpload} />
        {#if file}
          <div class="glass rounded-xl p-3 flex items-center justify-between">
            <span class="text-sm truncate">{file.name}</span>
            <span class="text-xs text-white/40">{(file.size / 1024 / 1024).toFixed(1)} MB</span>
          </div>
        {/if}
        <Button onclick={analyze} variant="gradient" size="lg" class="w-full" disabled={!file} loading={loading}>
          {loading ? $_('analyze.analyzing') : $_('analyze.analyzing').replace('...', '') + ' →'}
        </Button>
      </div>
    </Card>
    <div class="flex gap-3 justify-center">
      <a href="/analyze/audio" class="glass rounded-xl px-4 py-2 text-sm text-white/50 hover:text-white hover:bg-white/5 transition-colors">Audio Analysis</a>
      <a href="/analyze/text" class="glass rounded-xl px-4 py-2 text-sm text-white/50 hover:text-white hover:bg-white/5 transition-colors">Text Analysis</a>
    </div>
  {/if}

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {/if}

  {#if result}
    <div class="result-section space-y-6">
      <!-- Header -->
      <div class="flex flex-col md:flex-row items-start gap-6">
        <GradeBadge grade={result.overall_grade} />
        <div class="flex-1">
          <h2 class="text-xl font-bold">{result.filename}</h2>
          <p class="text-sm text-white/50">{result.summary}</p>
          <div class="flex gap-4 mt-2">
            <span class="text-xs text-white/30">{result.duration_sec.toFixed(1)}s</span>
            <span class="text-xs text-white/30">{result.media_type}</span>
            {#if result.tokens_used}
              <span class="text-xs text-dopamine-400">-{result.tokens_used} tokens</span>
            {/if}
          </div>
        </div>
      </div>

      <!-- Score Cards -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <ScoreCard label={$_('common.attention')} value={result.brain_scores.attention.overall} color="#4d6cf5" sublabel={result.brain_scores.attention.label} />
        <ScoreCard label={$_('common.dopamine')} value={result.brain_scores.dopamine.overall} color="#f59e0b" sublabel={result.brain_scores.dopamine.label} />
        <ScoreCard label={$_('common.memory')} value={result.brain_scores.memory.overall} color="#10b981" sublabel={result.brain_scores.memory.label} />
      </div>

      <!-- Charts Row -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 class="text-sm font-semibold mb-3">{$_('analyze.engagement_curve')}</h3>
          <div class="h-48">
            <EngagementCurve timestamps={result.timestamp_axis} scores={result.engagement_curve} />
          </div>
        </Card>
        <Card>
          <h3 class="text-sm font-semibold mb-3">{$_('analyze.roi_breakdown')}</h3>
          <div class="grid grid-cols-3 gap-4">
            <RoiBreakdown roi_breakdown={result.brain_scores.attention.roi_breakdown} color="#4d6cf5" />
            <RoiBreakdown roi_breakdown={result.brain_scores.dopamine.roi_breakdown} color="#f59e0b" />
            <RoiBreakdown roi_breakdown={result.brain_scores.memory.roi_breakdown} color="#10b981" />
          </div>
        </Card>
      </div>

      <!-- Radar + Brain -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <h3 class="text-sm font-semibold mb-3">Neural Profile</h3>
          <div class="h-56">
            <RadarChart values={[result.brain_scores.attention.overall, result.brain_scores.dopamine.overall, result.brain_scores.memory.overall]} />
          </div>
        </Card>
        <Card>
          <div class="flex items-center justify-between mb-3">
            <h3 class="text-sm font-semibold">{$_('analyze.brain_visualization')}</h3>
            <div class="flex gap-1">
              {#each ['attention', 'dopamine', 'memory'] as mode}
                <button onclick={() => brainMode = mode as 'attention' | 'dopamine' | 'memory'} class={`px-2 py-1 text-xs rounded-lg transition-colors ${brainMode === mode ? 'bg-neural-500/20 text-neural-300' : 'text-white/40 hover:text-white/60'}`}>
                  {mode}
                </button>
              {/each}
            </div>
          </div>
          <div class="h-56">
            <BrainViewer roiScores={{...result.brain_scores.attention.roi_breakdown, ...result.brain_scores.dopamine.roi_breakdown, ...result.brain_scores.memory.roi_breakdown}} mode={brainMode} />
          </div>
        </Card>
      </div>

      <!-- Recommendations -->
      {#if result.recommendations?.length}
        <Card>
          <h3 class="text-sm font-semibold mb-3">{$_('analyze.recommendations')} ({result.recommendations.length})</h3>
          <RecommendationList recommendations={result.recommendations} />
        </Card>
      {/if}

      <!-- Brain Viz Links -->
      {#if result.brain_viz_urls}
        <Card>
          <h3 class="text-sm font-semibold mb-3">Interactive Brain Views</h3>
          <div class="flex flex-wrap gap-2">
            {#each Object.entries(result.brain_viz_urls) as [mode, url]}
              <a href={url} target="_blank" class="glass rounded-xl px-4 py-2 text-sm hover:bg-white/5 transition-colors">{mode}</a>
            {/each}
          </div>
        </Card>
      {/if}

      <div class="flex justify-center">
        <Button onclick={() => { result = null; file = null; }} variant="secondary">Analyze Another Video</Button>
      </div>
    </div>
  {/if}
</div>
