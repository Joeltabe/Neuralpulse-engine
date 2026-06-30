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
  import VideoTimelineResult from '$lib/components/analysis/VideoTimelineResult.svelte';
  import AudienceInsights from '$lib/components/analysis/AudienceInsights.svelte';
  import ContentOptimization from '$lib/components/analysis/ContentOptimization.svelte';
  import ViralConfidence from '$lib/components/analysis/ViralConfidence.svelte';
  import GrowthTracker from '$lib/components/analysis/GrowthTracker.svelte';
  import { goto } from '$app/navigation';
  import { generateRecommendations, getContentProfile } from '$lib/utils/RecommendationEngine';
  import type { AnalysisResult } from '$lib/types/api';
  import type { RankedRecommendation, ContentProfile } from '$lib/utils/RecommendationEngine';

  let result = $state<AnalysisResult | null>(null);
  let loading = $state(true);
  let brainMode = $state<'attention' | 'dopamine' | 'memory'>('attention');
  let id = $derived($page.params.id);

  let mediaType = $state('');

  // Recommendation engine state
  let rankedRecommendations = $state<RankedRecommendation[]>([]);
  let contentProfile = $state<ContentProfile | null>(null);
  let highlightedRegion = $state('');

  async function load() {
    loading = true;
    try {
      const res = await fetch('/api/history/analyses');
      const data = await res.json();
      if (data.success) {
        const found = data.analyses.find((a: any) => a.id === id);
        if (found?.results) {
          result = found.results;
          mediaType = found.media_type || found.results.media_type || '';

          // Run TikTok/YouTube-inspired recommendation engine
          rankedRecommendations = generateRecommendations(found.results);
          contentProfile = getContentProfile(found.results);
        }
      }
    } catch { /* ignore */ }
    loading = false;
  }

  load();

  function openInEditor() {
    goto(`/editor?id=${id}`);
  }

  function handleRegionHover(region: string) {
    highlightedRegion = region;
  }

  // Content profile status labels
  function profileLabel(key: string, value: number): string {
    if (value > 0.7) return 'Strong';
    if (value > 0.4) return 'Moderate';
    return 'Weak';
  }

  function profileColor(value: number): string {
    if (value > 0.7) return 'text-emerald-400';
    if (value > 0.4) return 'text-amber-400';
    return 'text-red-400';
  }
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <a href="/history" class="text-sm text-white/40 hover:text-white transition-colors">&larr; {$_('common.back')}</a>

  {#if loading}
    <div class="flex justify-center py-16"><Spinner size="lg" /></div>
  {:else if result}
    <div class="flex items-start gap-6">
      <GradeBadge grade={result.overall_grade} />
      <div class="flex-1">
        <div class="flex items-center gap-3">
          <h1 class="text-xl font-bold">{result.filename}</h1>
    {#if mediaType === 'video'}
            <button onclick={openInEditor}
              class="px-3 py-1.5 rounded-lg bg-neural-500/15 hover:bg-neural-500/25 text-neural-400 text-xs font-medium transition-colors flex items-center gap-1.5"
            >
              <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/></svg>
              Open in Editor
            </button>
          {/if}
        </div>
        <p class="text-sm text-white/50 mt-1">{result.summary}</p>
      </div>
    </div>

    <!-- Preview Audience Banner -->
    <div class="glass rounded-xl p-4 border border-neural-500/15 bg-gradient-to-r from-neural-500/5 via-dopamine-500/5 to-memory-500/5">
      <div class="flex items-center gap-3">
        <div class="w-8 h-8 rounded-lg bg-neural-500/15 flex items-center justify-center shrink-0">
          <svg class="w-4 h-4 text-neural-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        </div>
        <div class="flex-1">
          <p class="text-xs font-semibold text-white/70">Neural Preview Audience</p>
          <p class="text-[11px] text-white/35 mt-0.5">This is how your first viewers' brains react — see exactly where attention holds, where dopamine fires, and what they'll remember before you post for the world.</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
          <span class="text-[10px] text-emerald-400 font-medium">Live Neural Scan</span>
        </div>
      </div>
    </div>

    {#if mediaType === 'video'}
      <Card>
        <VideoTimelineResult
          analysisId={id}
          recommendations={result.recommendations}
          engagementCurve={result.engagement_curve}
          timestampAxis={result.timestamp_axis}
          sceneBreaks={result.scene_breaks || []}
        />
      </Card>
    {/if}

    {#if result.audience_profile}
      <AudienceInsights profile={result.audience_profile} />
    {/if}

    {#if result.content_optimization}
      <ContentOptimization optimization={result.content_optimization} />
    {/if}

    {#if result.copyright_analysis}
      <ViralConfidence analysis={result.copyright_analysis} />
    {/if}

    {#if result.content_identity}
      <GrowthTracker identity={result.content_identity} currentScores={result.brain_scores} />
    {/if}

    <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
      <ScoreCard label={$_('common.attention')} value={result.brain_scores.attention.overall} color="#4d6cf5" />
      <ScoreCard label={$_('common.dopamine')} value={result.brain_scores.dopamine.overall} color="#f59e0b" />
      <ScoreCard label={$_('common.memory')} value={result.brain_scores.memory.overall} color="#10b981" />
    </div>
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card><div class="h-48"><EngagementCurve timestamps={result.timestamp_axis} scores={result.engagement_curve} /></div></Card>
      <Card><div class="h-56"><RadarChart values={[result.brain_scores.attention.overall, result.brain_scores.dopamine.overall, result.brain_scores.memory.overall]} /></div></Card>
    </div>

    <!-- Brain Visualization + Recommendations (connected) -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <Card>
        <div class="flex items-center justify-between mb-3">
          <div>
            <h3 class="text-sm font-semibold">{$_('analyze.brain_visualization')}</h3>
            <p class="text-[10px] text-white/30 mt-0.5">Colored regions = affected areas · Grey = inactive · Hover recommendations to highlight</p>
          </div>
          <div class="flex gap-1">
            {#each ['attention', 'dopamine', 'memory'] as mode}
              <button onclick={() => brainMode = mode as 'attention' | 'dopamine' | 'memory'} class={`px-2 py-1 text-xs rounded-lg transition-colors ${brainMode === mode ? 'bg-neural-500/20 text-neural-300' : 'text-white/40'}`}>{mode}</button>
            {/each}
          </div>
        </div>
        <div class="h-64">
          <BrainViewer
            roiScores={{...result.brain_scores.attention.roi_breakdown, ...result.brain_scores.dopamine.roi_breakdown, ...result.brain_scores.memory.roi_breakdown}}
            mode={brainMode}
            highlightRegion={highlightedRegion}
          />
        </div>
      </Card>

      <!-- Neural Recommendations (TikTok/YouTube-inspired ranking) -->
      <Card>
        <div class="flex items-center justify-between mb-3">
          <div>
            <h3 class="text-sm font-semibold">Neural Recommendations</h3>
            <p class="text-[10px] text-white/30 mt-0.5">{rankedRecommendations.length} insights ranked by predicted neural impact</p>
          </div>
          {#if rankedRecommendations.length > 0}
            <div class="flex items-center gap-1.5">
              <span class="text-[9px] text-white/20 uppercase tracking-wider">Powered by</span>
              <span class="text-[9px] text-neural-400 font-medium">Interest Graph Engine</span>
            </div>
          {/if}
        </div>
        <div class="max-h-[600px] overflow-y-auto pr-1 -mr-1 custom-scrollbar">
          <RecommendationList
            recommendations={rankedRecommendations}
            onRegionHover={handleRegionHover}
          />
        </div>
      </Card>
    </div>

    <!-- Content Profile Summary (from the recommendation engine) -->
    {#if contentProfile}
      <Card>
        <h3 class="text-sm font-semibold mb-4">Content Neural Profile</h3>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          {#each [
            { label: 'Attention Capture', value: contentProfile.attention_mean, icon: '👁️' },
            { label: 'Reward Circuit', value: contentProfile.dopamine_mean, icon: '⚡' },
            { label: 'Memory Encoding', value: contentProfile.memory_mean, icon: '🧠' },
            { label: 'Engagement Trend', value: Math.max(0, 0.5 + contentProfile.engagement_trend), icon: '📈' },
            { label: 'Pacing Score', value: contentProfile.pacing_score, icon: '🎬' },
            { label: 'Encoding Depth', value: contentProfile.memory_encoding_depth, icon: '💾' },
            { label: 'Volatility', value: contentProfile.engagement_volatility, icon: '📊' },
            { label: 'Dopamine Gaps', value: 1 - contentProfile.dopamine_gap_score, icon: '🎯' }
          ] as metric}
            <div class="rounded-lg bg-white/[0.03] border border-white/5 p-3">
              <div class="flex items-center gap-1.5 mb-2">
                <span class="text-sm">{metric.icon}</span>
                <span class="text-[10px] text-white/40 uppercase tracking-wider">{metric.label}</span>
              </div>
              <div class="flex items-center gap-2">
                <div class="flex-1 h-1.5 rounded-full bg-white/5 overflow-hidden">
                  <div
                    class="h-full rounded-full transition-all duration-700"
                    style="width: {Math.min(100, metric.value * 100)}%; background: linear-gradient(90deg, {metric.value > 0.7 ? '#10b981' : metric.value > 0.4 ? '#f59e0b' : '#ef4444'}80, {metric.value > 0.7 ? '#10b981' : metric.value > 0.4 ? '#f59e0b' : '#ef4444'});"
                  ></div>
                </div>
                <span class="text-xs font-bold {profileColor(metric.value)} tabular-nums">{(metric.value * 100).toFixed(0)}%</span>
              </div>
              <span class="text-[9px] {profileColor(metric.value)} mt-1 block">{profileLabel(metric.label, metric.value)}</span>
            </div>
          {/each}
        </div>
      </Card>
    {/if}
  {:else}
    <Card class="text-center py-12"><p class="text-white/40">Result not found</p></Card>
  {/if}
</div>

<style>
  .custom-scrollbar::-webkit-scrollbar {
    width: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-track {
    background: transparent;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.08);
    border-radius: 4px;
  }
  .custom-scrollbar::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.15);
  }
</style>
