<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Tabs from '$lib/components/ui/Tabs.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import { error as showError } from '$lib/stores/notifications';

  type TabId = 'search' | 'channel' | 'trending';

  interface SearchItem {
    video_id?: string;
    channel_id?: string;
    playlist_id?: string;
    title: string;
    description: string;
    thumbnail_url: string;
    published_at: string;
    channel_title: string;
    kind: string;
  }

  interface ChannelInfo {
    channel_id: string;
    title: string;
    description: string;
    subscriber_count: number;
    video_count: number;
    view_count: number;
    country: string | null;
    thumbnail_url: string;
    topic_ids: string[];
    is_verified: boolean;
  }

  interface FrameAnalysisData {
    frames: Array<{
      index: number;
      timestamp_sec: number;
      attention: number;
      dopamine: number;
      memory: number;
      engagement: number;
      motion: number;
      visual_complexity: number;
      is_scene_boundary: boolean;
    }>;
    engagement_curve: number[];
    timestamp_axis: number[];
    scene_changes: number[];
    keyframes: Array<{
      index: number;
      timestamp_sec: number;
      engagement: number;
      attention: number;
      dopamine: number;
      memory: number;
    }>;
    highlight_segments: Array<{
      start: number;
      end: number;
      duration: number;
      peak_engagement: number;
      avg_engagement: number;
      frame_count: number;
      rank: number;
    }>;
    overall_stats: {
      avg_attention: number;
      avg_dopamine: number;
      avg_memory: number;
      avg_engagement: number;
      peak_engagement: number;
      min_engagement: number;
      engagement_std: number;
      n_scene_changes: number;
      n_frames_analyzed: number;
      n_highlight_segments: number;
    };
    duration_sec: number;
    total_frames: number;
    fps_analyzed: number;
  }

  interface VideoAnalysis {
    video: {
      video_id: string;
      title: string;
      channel_title: string;
      duration_sec: number;
      view_count: number;
      like_count: number;
      comment_count: number;
      engagement_rate: number;
      thumbnail_url: string;
    };
    analysis: {
      brain_scores: {
        attention: { overall: number; label: string };
        dopamine: { overall: number; label: string };
        memory: { overall: number; label: string };
      };
      summary: string;
      overall_grade: string;
      viral_score: number;
      recommendations: Array<{ timestamp_sec: number; severity: string; message: string }>;
    };
    viral_score: number;
    frame_analysis?: FrameAnalysisData;
  }

  let activeTab: TabId = $state('search');
  let searchQuery = $state('');
  let searchResults = $state<SearchItem[]>([]);
  let searchLoading = $state(false);
  let channelId = $state('');
  let channelInfo = $state<ChannelInfo | null>(null);
  let channelLoading = $state(false);
  let trending = $state<SearchItem[]>([]);
  let trendingLoading = $state(false);
  let categories = $state<{ id: string; title: string }[]>([]);
  let selectedCategory = $state('');
  let resultsVisible = $state(false);
  let analyzing = $state<string | null>(null);
  let analyzingDeep = $state<string | null>(null);
  let analysisResult = $state<VideoAnalysis | null>(null);
  let analysisError = $state('');

  const tabs: { id: TabId; label: string }[] = [
    { id: 'search', label: 'Search' },
    { id: 'channel', label: 'Channel Lookup' },
    { id: 'trending', label: 'Trending' },
  ];

  async function doSearch() {
    if (!searchQuery.trim()) return;
    searchLoading = true;
    resultsVisible = false;
    try {
      const res = await fetch(`/api/youtube/search?q=${encodeURIComponent(searchQuery)}&max_results=20`);
      const data = await res.json();
      if (data.success) {
        searchResults = data.results || [];
        resultsVisible = true;
      } else {
        showError(data.error || 'Search failed');
      }
    } catch {
      showError('Network error');
    } finally {
      searchLoading = false;
    }
  }

  async function lookupChannel() {
    if (!channelId.trim()) return;
    channelLoading = true;
    channelInfo = null;
    try {
      const handle = channelId.trim().replace('@', '');
      const isId = handle.startsWith('UC');
      const url = isId
        ? `/api/youtube/channel/${handle}`
        : `/api/youtube/channel/handle/${encodeURIComponent(handle)}`;
      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        channelInfo = data.channel;
      } else {
        showError(data.error || 'Channel not found');
      }
    } catch {
      showError('Network error');
    } finally {
      channelLoading = false;
    }
  }

  async function loadTrending() {
    trendingLoading = true;
    try {
      const url = selectedCategory
        ? `/api/youtube/popular?category_id=${selectedCategory}&max_results=15`
        : '/api/youtube/popular?max_results=15';
      const res = await fetch(url);
      const data = await res.json();
      if (data.success) {
        trending = data.results || [];
      }
    } catch {
      showError('Network error');
    } finally {
      trendingLoading = false;
    }
  }

  async function loadCategories() {
    try {
      const res = await fetch('/api/youtube/categories');
      const data = await res.json();
      if (data.success) {
        categories = data.categories || [];
      }
    } catch { /* silent */ }
  }

  function formatCount(n: number): string {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return n.toString();
  }

  async function analyzeVideo(videoId: string) {
    analyzing = videoId;
    analyzingDeep = null;
    analysisResult = null;
    analysisError = '';
    try {
      const res = await fetch(`/api/youtube/analyze?video_id=${videoId}`);
      const data = await res.json();
      if (data.success) {
        analysisResult = data as VideoAnalysis;
      } else {
        analysisError = data.error || 'Analysis failed';
      }
    } catch {
      analysisError = 'Network error';
    } finally {
      analyzing = null;
    }
  }

  async function deepAnalyze(videoId: string) {
    analyzingDeep = videoId;
    analysisResult = null;
    analysisError = '';
    try {
      const res = await fetch(`/api/youtube/analyze?video_id=${videoId}&deep=true`);
      const data = await res.json();
      if (data.success) {
        analysisResult = data as VideoAnalysis;
      } else {
        analysisError = data.error || 'Deep analysis failed';
      }
    } catch {
      analysisError = 'Network error';
    } finally {
      analyzingDeep = null;
    }
  }

  function formatDuration(sec: number): string {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  }

  function timeAgo(dateStr: string): string {
    const d = new Date(dateStr);
    const now = new Date();
    const sec = Math.floor((now.getTime() - d.getTime()) / 1000);
    if (sec < 60) return 'just now';
    const min = Math.floor(sec / 60);
    if (min < 60) return `${min}m ago`;
    const hr = Math.floor(min / 60);
    if (hr < 24) return `${hr}h ago`;
    const days = Math.floor(hr / 24);
    if (days < 30) return `${days}d ago`;
    return d.toLocaleDateString();
  }

  onMount(() => {
    gsap.from('.yt-hero', { opacity: 0, y: 30, duration: 0.5, ease: 'power3.out' });
    loadCategories();
  });

  $effect(() => {
    if (activeTab === 'trending' && trending.length === 0) {
      loadTrending();
    }
  });
</script>

<div class="max-w-6xl mx-auto space-y-6">
  <div class="yt-hero">
    <div class="flex items-center gap-3">
      <div class="w-10 h-10 rounded-xl bg-red-500/15 flex items-center justify-center">
        <svg class="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0C.488 3.45.029 5.804 0 12c.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0C23.512 20.55 23.971 18.196 24 12c-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 4-8 4z"/>
        </svg>
      </div>
      <div>
        <h1 class="text-2xl font-bold">YouTube Analytics</h1>
        <p class="text-white/50 mt-1">Search content, analyze channels, and discover trending videos</p>
      </div>
    </div>
  </div>

  <Tabs
    items={tabs}
    bind:active={activeTab}
    class="bg-white/[0.03] rounded-xl p-1"
  />

  {#if activeTab === 'search'}
    <Card>
      <div class="space-y-4">
        <div class="flex gap-3">
          <div class="flex-1">
            <Input
              placeholder="Search YouTube videos, channels, playlists..."
              bind:value={searchQuery}
              onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && doSearch()}
            />
          </div>
          <Button onclick={doSearch} variant="gradient" disabled={!searchQuery.trim() || searchLoading}>
            {searchLoading ? 'Searching...' : 'Search'}
          </Button>
        </div>
      </div>
    </Card>

    {#if searchLoading}
      <Card><div class="flex justify-center py-8"><Spinner size="lg" /></div></Card>
    {/if}

    {#if resultsVisible && searchResults.length > 0}
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {#each searchResults as item}
          <Card class="overflow-hidden p-0">
            <div class="aspect-video bg-surface-800 relative overflow-hidden">
              {#if item.thumbnail_url}
                <img src={item.thumbnail_url} alt={item.title} class="w-full h-full object-cover" />
              {/if}
              <div class="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/60 text-[10px] uppercase tracking-wider">
                {item.kind}
              </div>
            </div>
            <div class="p-3 space-y-1.5">
              <h3 class="text-sm font-semibold line-clamp-2 leading-snug">{item.title}</h3>
              <p class="text-xs text-white/40 line-clamp-2">{item.description}</p>
              <div class="flex items-center justify-between text-[10px] text-white/30">
                <span>{item.channel_title}</span>
                <span>{timeAgo(item.published_at)}</span>
              </div>
              {#if item.video_id}
                <div class="mt-2 flex gap-1.5">
                  <button
                    onclick={() => analyzeVideo(item.video_id!)}
                    disabled={analyzing === item.video_id || analyzingDeep === item.video_id}
                    class="flex-1 px-3 py-1.5 rounded-xl bg-gradient-to-r from-red-500/20 to-orange-500/20 hover:from-red-500/30 hover:to-orange-500/30 text-[10px] font-medium text-red-300 transition-all disabled:opacity-50 disabled:cursor-wait"
                  >
                    {analyzing === item.video_id ? 'Analyzing...' : 'Quick'}
                  </button>
                  <button
                    onclick={() => deepAnalyze(item.video_id!)}
                    disabled={analyzingDeep === item.video_id || analyzing === item.video_id}
                    class="flex-1 px-3 py-1.5 rounded-xl bg-gradient-to-r from-purple-500/20 to-blue-500/20 hover:from-purple-500/30 hover:to-blue-500/30 text-[10px] font-medium text-purple-300 transition-all disabled:opacity-50 disabled:cursor-wait"
                  >
                    {analyzingDeep === item.video_id ? 'Deep...' : 'Deep'}
                  </button>
                </div>
              {/if}
            </div>
          </Card>
        {/each}
      </div>
    {:else if resultsVisible}
      <Card><p class="text-white/40 text-center py-6">No results found</p></Card>
    {/if}

    {#if analysisResult}
      <Card class="mt-6">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-lg font-bold">Analysis: {analysisResult.video.title}</h2>
          <button
            onclick={() => analysisResult = null}
            class="text-white/30 hover:text-white/60 text-sm"
          >✕</button>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div class="lg:col-span-2 space-y-4">
            <div class="flex gap-2">
              {#if analysisResult.video.thumbnail_url}
                <img src={analysisResult.video.thumbnail_url} alt={analysisResult.video.title}
                     class="w-44 h-24 rounded-xl object-cover flex-shrink-0" />
              {/if}
              <div class="space-y-1 text-sm">
                <p class="text-white/60"><span class="text-white/80 font-medium">{analysisResult.video.channel_title}</span></p>
                <p class="text-[10px] text-white/30">{analysisResult.video.view_count.toLocaleString()} views · {formatDuration(analysisResult.video.duration_sec)} · {analysisResult.video.engagement_rate}% engagement</p>
                <p class="text-[10px] text-white/30">{analysisResult.video.like_count.toLocaleString()} likes · {analysisResult.video.comment_count.toLocaleString()} comments</p>
              </div>
            </div>
            <div class="flex gap-3">
              <div class="flex-1 bg-white/[0.03] rounded-xl p-3 text-center">
                <div class="text-2xl font-bold text-blue-400">{(analysisResult.analysis.brain_scores.attention.overall * 100).toFixed(0)}%</div>
                <div class="text-[10px] text-white/40">Attention</div>
                <div class="text-[9px] text-white/20">{analysisResult.analysis.brain_scores.attention.label}</div>
              </div>
              <div class="flex-1 bg-white/[0.03] rounded-xl p-3 text-center">
                <div class="text-2xl font-bold text-green-400">{(analysisResult.analysis.brain_scores.dopamine.overall * 100).toFixed(0)}%</div>
                <div class="text-[10px] text-white/40">Dopamine</div>
                <div class="text-[9px] text-white/20">{analysisResult.analysis.brain_scores.dopamine.label}</div>
              </div>
              <div class="flex-1 bg-white/[0.03] rounded-xl p-3 text-center">
                <div class="text-2xl font-bold text-purple-400">{(analysisResult.analysis.brain_scores.memory.overall * 100).toFixed(0)}%</div>
                <div class="text-[10px] text-white/40">Memory</div>
                <div class="text-[9px] text-white/20">{analysisResult.analysis.brain_scores.memory.label}</div>
              </div>
              <div class="flex-1 bg-white/[0.03] rounded-xl p-3 text-center">
                <div class="text-2xl font-bold text-orange-400">{(analysisResult.viral_score * 100).toFixed(0)}%</div>
                <div class="text-[10px] text-white/40">Viral</div>
                <div class="text-[9px] text-white/20">Score</div>
              </div>
            </div>
            {#if analysisResult.analysis.summary}
              <p class="text-sm text-white/60 leading-relaxed">{analysisResult.analysis.summary}</p>
            {/if}
            {#if analysisResult.analysis.overall_grade}
              <div class="bg-white/[0.03] rounded-xl px-4 py-2 text-sm">
                <span class="text-white/40">Grade: </span>
                <span class="font-bold text-white/80">{analysisResult.analysis.overall_grade}</span>
              </div>
            {/if}
          </div>
          {#if analysisResult.analysis.recommendations?.length > 0}
            <div class="space-y-2">
              <h3 class="text-sm font-semibold text-white/60">Recommendations</h3>
              {#each analysisResult.analysis.recommendations as rec}
                <div class="bg-white/[0.03] rounded-lg px-3 py-2 text-xs">
                  <span class="text-white/30">t={rec.timestamp_sec}s · </span>
                  <span class="text-white/60">{rec.message}</span>
                  <span class="block text-[9px] mt-0.5 text-white/20">{rec.severity}</span>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        {#if analysisResult.frame_analysis}
          <hr class="border-white/10 my-4">
          <div class="space-y-4">
            <h3 class="text-md font-bold flex items-center gap-2">
              <span class="w-2 h-2 rounded-full bg-purple-400"></span>
              DINOv2 Frame Analysis
              <span class="text-[10px] text-white/30 font-normal">({analysisResult.frame_analysis.overall_stats.n_frames_analyzed} frames @ {analysisResult.frame_analysis.fps_analyzed}fps)</span>
            </h3>

            <div class="grid grid-cols-2 sm:grid-cols-5 gap-2">
              <div class="bg-white/[0.03] rounded-xl p-2 text-center">
                <div class="text-lg font-bold text-purple-400">{(analysisResult.frame_analysis.overall_stats.avg_engagement * 100).toFixed(0)}%</div>
                <div class="text-[9px] text-white/40">Avg Engagement</div>
              </div>
              <div class="bg-white/[0.03] rounded-xl p-2 text-center">
                <div class="text-lg font-bold text-blue-400">{(analysisResult.frame_analysis.overall_stats.avg_attention * 100).toFixed(0)}%</div>
                <div class="text-[9px] text-white/40">Avg Attention</div>
              </div>
              <div class="bg-white/[0.03] rounded-xl p-2 text-center">
                <div class="text-lg font-bold text-green-400">{(analysisResult.frame_analysis.overall_stats.avg_dopamine * 100).toFixed(0)}%</div>
                <div class="text-[9px] text-white/40">Avg Dopamine</div>
              </div>
              <div class="bg-white/[0.03] rounded-xl p-2 text-center">
                <div class="text-lg font-bold text-purple-300">{(analysisResult.frame_analysis.overall_stats.avg_memory * 100).toFixed(0)}%</div>
                <div class="text-[9px] text-white/40">Avg Memory</div>
              </div>
              <div class="bg-white/[0.03] rounded-xl p-2 text-center">
                <div class="text-lg font-bold text-orange-400">{(analysisResult.frame_analysis.overall_stats.peak_engagement * 100).toFixed(0)}%</div>
                <div class="text-[9px] text-white/40">Peak Engage</div>
              </div>
            </div>

            {#if analysisResult.frame_analysis.highlight_segments.length > 0}
              <div>
                <h4 class="text-sm font-semibold text-white/60 mb-2">Top Highlight Segments</h4>
                <div class="space-y-1.5">
                  {#each analysisResult.frame_analysis.highlight_segments.filter(s => s.rank <= 5) as seg}
                    <div class="flex items-center gap-3 bg-white/[0.02] rounded-lg px-3 py-2">
                      <span class="text-[10px] font-bold text-white/20 w-4">#{seg.rank}</span>
                      <div class="flex-1">
                        <div class="text-xs text-white/70">{formatDuration(seg.start)} – {formatDuration(seg.end)}</div>
                        <div class="text-[9px] text-white/30">{seg.duration}s · {seg.frame_count} frames</div>
                      </div>
                      <div class="text-right">
                        <div class="text-xs font-bold text-green-400">{(seg.avg_engagement * 100).toFixed(0)}%</div>
                        <div class="text-[9px] text-white/30">avg</div>
                      </div>
                      <div class="w-16 bg-white/5 rounded-full h-1.5">
                        <div class="h-full rounded-full bg-gradient-to-r from-green-500 to-emerald-400" style="width: {seg.avg_engagement * 100}%"></div>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if analysisResult.frame_analysis.keyframes.length > 0}
              <div>
                <h4 class="text-sm font-semibold text-white/60 mb-2">Keyframes (Highest Engagement)</h4>
                <div class="grid grid-cols-5 gap-2">
                  {#each analysisResult.frame_analysis.keyframes as kf}
                    <div class="bg-white/[0.03] rounded-lg p-1.5 text-center">
                      <div class="text-lg font-bold text-white/80">{formatDuration(kf.timestamp_sec)}</div>
                      <div class="text-[9px] text-white/30">{(kf.engagement * 100).toFixed(0)}%</div>
                      <div class="flex justify-center gap-1 mt-1">
                        <span class="w-1.5 h-1.5 rounded-full bg-blue-400" title="attention"></span>
                        <span class="w-1.5 h-1.5 rounded-full bg-green-400" title="dopamine"></span>
                        <span class="w-1.5 h-1.5 rounded-full bg-purple-400" title="memory"></span>
                      </div>
                    </div>
                  {/each}
                </div>
              </div>
            {/if}

            {#if analysisResult.frame_analysis.scene_changes.length > 0}
              <div>
                <h4 class="text-sm font-semibold text-white/60 mb-2">Scene Changes ({analysisResult.frame_analysis.scene_changes.length})</h4>
                <div class="flex flex-wrap gap-1">
                  {#each analysisResult.frame_analysis.scene_changes as ts}
                    <span class="px-2 py-0.5 rounded bg-white/5 text-[10px] text-white/40">{formatDuration(ts)}</span>
                  {/each}
                </div>
              </div>
            {/if}

            <div class="text-[10px] text-white/20">
              Model: facebook/dinov2-base · Per-frame engagement from CLS + patch + motion features
            </div>
          </div>
        {/if}
      </Card>
    {/if}
    {#if analysisError}
      <Card class="mt-4"><p class="text-red-400 text-sm">{analysisError}</p></Card>
    {/if}
  {/if}

  {#if activeTab === 'channel'}
    <Card>
      <div class="space-y-4">
        <div class="flex gap-3">
          <div class="flex-1">
            <Input
              placeholder="Channel ID (UCxxx) or @handle"
              bind:value={channelId}
              onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && lookupChannel()}
            />
          </div>
          <Button onclick={lookupChannel} variant="gradient" disabled={!channelId.trim() || channelLoading}>
            {channelLoading ? 'Looking up...' : 'Lookup'}
          </Button>
        </div>
      </div>
    </Card>

    {#if channelLoading}
      <Card><div class="flex justify-center py-8"><Spinner size="lg" /></div></Card>
    {/if}

    {#if channelInfo}
      <Card>
        <div class="flex flex-col sm:flex-row gap-5 items-start">
          <div class="relative flex-shrink-0">
            {#if channelInfo.thumbnail_url}
              <img src={channelInfo.thumbnail_url} alt={channelInfo.title}
                   class="w-24 h-24 rounded-2xl object-cover border border-white/10" />
            {:else}
              <div class="w-24 h-24 rounded-2xl bg-gradient-to-br from-red-500/30 to-orange-500/30 flex items-center justify-center">
                <svg class="w-10 h-10 text-white/60" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0C.488 3.45.029 5.804 0 12c.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0C23.512 20.55 23.971 18.196 24 12c-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 4-8 4z"/>
                </svg>
              </div>
            {/if}
            {#if channelInfo.is_verified}
              <div class="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-blue-500 flex items-center justify-center">
                <svg class="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
                </svg>
              </div>
            {/if}
          </div>
          <div class="flex-1 min-w-0">
            <h2 class="text-xl font-bold">{channelInfo.title}</h2>
            <p class="text-xs text-white/30">@{channelInfo.channel_id}</p>
            <div class="flex flex-wrap gap-5 mt-2">
              <span class="text-sm text-white/60">
                <span class="font-semibold text-white/80">{formatCount(channelInfo.subscriber_count)}</span> subscribers
              </span>
              <span class="text-sm text-white/60">
                <span class="font-semibold text-white/80">{formatCount(channelInfo.video_count)}</span> videos
              </span>
              <span class="text-sm text-white/60">
                <span class="font-semibold text-white/80">{formatCount(channelInfo.view_count)}</span> views
              </span>
              {#if channelInfo.country}
                <span class="text-sm text-white/60">📍 {channelInfo.country}</span>
              {/if}
            </div>
            {#if channelInfo.description}
              <p class="text-sm text-white/40 mt-2 line-clamp-2">{channelInfo.description}</p>
            {/if}
            {#if channelInfo.topic_ids && channelInfo.topic_ids.length > 0}
              <div class="flex gap-2 mt-3">
                {#each channelInfo.topic_ids.slice(0, 3) as tid}
                  <span class="px-2 py-0.5 rounded-full bg-white/5 text-[10px] text-white/40">{tid}</span>
                {/each}
              </div>
            {/if}
          </div>
        </div>
      </Card>
    {/if}
  {/if}

  {#if activeTab === 'trending'}
    <Card>
      <div class="flex items-center gap-3 flex-wrap">
        <div class="flex-1 min-w-[200px]">
          <select
            bind:value={selectedCategory}
            onchange={loadTrending}
            class="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-sm text-white outline-none focus:border-red-500/30"
          >
            <option value="">All Categories</option>
            {#each categories as cat}
              <option value={cat.id}>{cat.title}</option>
            {/each}
          </select>
        </div>
        <Button onclick={loadTrending} variant="primary" disabled={trendingLoading}>
          {trendingLoading ? 'Loading...' : 'Refresh'}
        </Button>
      </div>
    </Card>

    {#if trendingLoading}
      <Card><div class="flex justify-center py-8"><Spinner size="lg" /></div></Card>
    {/if}

    {#if trending.length > 0}
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
        {#each trending as item}
          <Card class="overflow-hidden p-0">
            <div class="aspect-video bg-surface-800 relative overflow-hidden">
              {#if item.thumbnail_url}
                <img src={item.thumbnail_url} alt={item.title} class="w-full h-full object-cover" />
              {/if}
            </div>
            <div class="p-3 space-y-1.5">
              <h3 class="text-sm font-semibold line-clamp-2 leading-snug">{item.title}</h3>
              <p class="text-xs text-white/40 line-clamp-2">{item.description}</p>
              <div class="flex items-center justify-between text-[10px] text-white/30">
                <span>{item.channel_title}</span>
                <span>{timeAgo(item.published_at)}</span>
              </div>
              {#if typeof item.video_id === 'string'}
                <div class="flex gap-1.5 pt-1">
                  <button
                    onclick={() => analyzeVideo(item.video_id!)}
                    disabled={analyzing === item.video_id || analyzingDeep === item.video_id}
                    class="flex-1 px-2 py-1 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-[9px] font-medium text-red-300 transition-all disabled:opacity-50"
                  >
                    {analyzing === item.video_id ? '...' : 'Quick'}
                  </button>
                  <button
                    onclick={() => deepAnalyze(item.video_id!)}
                    disabled={analyzingDeep === item.video_id || analyzing === item.video_id}
                    class="flex-1 px-2 py-1 rounded-lg bg-purple-500/10 hover:bg-purple-500/20 text-[9px] font-medium text-purple-300 transition-all disabled:opacity-50"
                  >
                    {analyzingDeep === item.video_id ? '...' : 'Deep'}
                  </button>
                </div>
              {/if}
            </div>
          </Card>
        {/each}
      </div>
    {:else if !trendingLoading}
      <Card><p class="text-white/40 text-center py-6">No trending data loaded</p></Card>
    {/if}
  {/if}
</div>
