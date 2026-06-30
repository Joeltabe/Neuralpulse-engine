<script lang="ts">
  import { onMount } from 'svelte';
  import { gsap } from 'gsap';
  import { page } from '$app/stores';
  import Card from '$lib/components/ui/Card.svelte';
  import Button from '$lib/components/ui/Button.svelte';
  import Input from '$lib/components/ui/Input.svelte';
  import Spinner from '$lib/components/ui/Spinner.svelte';
  import Badge from '$lib/components/ui/Badge.svelte';
  import type { ChannelProfile, ChannelLinkResponse } from '$lib/types/api';
  import { success, error as showError } from '$lib/stores/notifications';

  let url = $state('');
  let loading = $state(false);
  let profile = $state<ChannelProfile | null>(null);
  let saved = $state(false);

  function detectPlatform(u: string): string {
    const l = u.toLowerCase();
    if (l.includes('youtube.com') || l.includes('youtu.be')) return 'youtube';
    if (l.includes('tiktok.com')) return 'tiktok';
    return '';
  }

  async function analyze() {
    if (!url.trim()) return;
    loading = true;
    saved = false;
    try {
      const res = await fetch('/api/channel/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() })
      });
      const data: ChannelLinkResponse = await res.json();
      if (data.success && data.profile) {
        profile = data.profile;
      } else {
        showError(data.error || 'Failed to analyze channel');
      }
    } catch {
      showError('Network error');
    } finally {
      loading = false;
    }
  }

  async function linkChannel() {
    if (!profile) return;
    loading = true;
    try {
      const res = await fetch('/api/channel/link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url.trim() })
      });
      const data: ChannelLinkResponse = await res.json();
      if (data.success) {
        saved = true;
        profile = data.profile || profile;
        success('Channel linked — recommendations now personalized');
      } else {
        showError(data.error || 'Failed to link channel');
      }
    } catch {
      showError('Network error');
    } finally {
      loading = false;
    }
  }

  async function loadProfile() {
    try {
      const res = await fetch('/api/channel/profile');
      const data: ChannelLinkResponse = await res.json();
      if (data.success && data.profile) {
        profile = data.profile;
        saved = true;
      }
    } catch { /* no linked channel */ }
  }

  function platformIcon(): string {
    if (!profile) return '';
    if (profile.platform === 'youtube') return 'M19.615 3.184c-3.604-.246-11.631-.245-15.23 0C.488 3.45.029 5.804 0 12c.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0C23.512 20.55 23.971 18.196 24 12c-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 4-8 4z';
    return 'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z';
  }

  function nicheColor(niche: string): string {
    const colors: Record<string, string> = {
      gaming: 'bg-green-500/20 text-green-300',
      music: 'bg-purple-500/20 text-purple-300',
      education: 'bg-blue-500/20 text-blue-300',
      technology: 'bg-cyan-500/20 text-cyan-300',
      entertainment: 'bg-yellow-500/20 text-yellow-300',
      lifestyle: 'bg-pink-500/20 text-pink-300',
      news: 'bg-red-500/20 text-red-300',
      sports: 'bg-orange-500/20 text-orange-300',
    };
    return colors[niche] || 'bg-white/10 text-white/60';
  }

  function formatCount(n: number): string {
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
    if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
    return n.toString();
  }

  onMount(() => {
    loadProfile();
    gsap.from('.channel-hero', { opacity: 0, y: 30, duration: 0.6, ease: 'power3.out' });
  });
</script>

<div class="max-w-4xl mx-auto space-y-6">
  <div class="channel-hero">
    <h1 class="text-2xl font-bold">Your Channel</h1>
    <p class="text-white/50 mt-1">Link your YouTube or TikTok to get personalized, niche-aware recommendations</p>
  </div>

  <Card>
    <div class="space-y-4">
      <Input
        label="Channel URL"
        placeholder="https://youtube.com/@channel or https://tiktok.com/@username"
        bind:value={url}
      />
      <div class="flex items-center gap-3">
        <Button onclick={analyze} variant="gradient" size="lg" disabled={!url.trim() || loading}>
          {loading ? 'Analyzing...' : 'Analyze Channel'}
        </Button>
        {#if detectPlatform(url)}
          <Badge
            class={detectPlatform(url) === 'youtube'
              ? 'border-red-500/30 text-red-300'
              : 'border-purple-500/30 text-purple-300'}
          >
            {detectPlatform(url) === 'youtube' ? 'YouTube' : 'TikTok'}
          </Badge>
        {/if}
      </div>
    </div>
  </Card>

  {#if loading}
    <Card>
      <div class="flex items-center justify-center py-12">
        <Spinner size="lg" />
      </div>
    </Card>
  {/if}

  {#if profile && !loading}
    <Card>
      <div class="flex flex-col sm:flex-row gap-6 items-start">
        <div class="relative flex-shrink-0">
          {#if profile.avatar_url}
            <img
              src={profile.avatar_url}
              alt={profile.channel_name}
              class="w-20 h-20 rounded-2xl object-cover border border-white/10"
            />
          {:else}
            <div class="w-20 h-20 rounded-2xl bg-gradient-to-br from-neural-500/30 to-dopamine-500/30 flex items-center justify-center">
              <svg class="w-8 h-8 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d={platformIcon()}/>
              </svg>
            </div>
          {/if}
          <div class="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-surface-900 flex items-center justify-center">
            <svg class="w-3.5 h-3.5 {profile.platform === 'youtube' ? 'text-red-400' : 'text-purple-400'}" fill="currentColor" viewBox="0 0 24 24">
              <path d={platformIcon()}/>
            </svg>
          </div>
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 flex-wrap">
            <h2 class="text-xl font-bold truncate">{profile.channel_name}</h2>
            <span class="text-xs text-white/30">@{profile.channel_id}</span>
          </div>
          <div class="flex flex-wrap gap-4 mt-2">
            <span class="text-sm text-white/60">
              <span class="font-semibold text-white/80">{formatCount(profile.subscriber_count)}</span> subscribers
            </span>
            <span class="text-sm text-white/60">
              <span class="font-semibold text-white/80">{formatCount(profile.video_count)}</span> videos
            </span>
            {#if profile.country}
              <span class="text-sm text-white/60">📍 {profile.country}</span>
            {/if}
          </div>
          {#if profile.description}
            <p class="text-sm text-white/40 mt-2 line-clamp-2">{profile.description}</p>
          {/if}
          <div class="flex flex-wrap gap-2 mt-3">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-medium {nicheColor(profile.niche)}">
              {profile.niche}
            </span>
            {#if profile.niche_confidence > 0}
              <span class="text-xs text-white/30">
                {(profile.niche_confidence * 100).toFixed(0)}% confidence
              </span>
            {/if}
            {#if profile.engagement_rate}
              <span class="text-xs text-dopamine-400">
                {(profile.engagement_rate * 100).toFixed(1)}% engagement rate
              </span>
            {/if}
          </div>
        </div>
      </div>

      {#if profile.recent_tags && profile.recent_tags.length > 0}
        <div class="mt-4 pt-4 border-t border-white/5">
          <p class="text-xs font-semibold text-white/40 mb-2 uppercase tracking-wider">Content Tags</p>
          <div class="flex flex-wrap gap-1.5">
            {#each profile.recent_tags.slice(0, 12) as tag}
              <span class="px-2 py-0.5 rounded-md bg-white/5 text-xs text-white/50">#{tag}</span>
            {/each}
          </div>
        </div>
      {/if}

      <div class="mt-6 pt-4 border-t border-white/5 flex items-center justify-between">
        <div class="text-xs text-white/30">
          {#if saved}
            <span class="text-emerald-400">✓ Linked — recommendations will use your {profile.platform} niche data</span>
          {:else}
            Link to personalize recommendations
          {/if}
        </div>
        <Button onclick={linkChannel} variant="primary" disabled={loading || saved}>
          {saved ? 'Linked ✓' : 'Link Channel'}
        </Button>
      </div>
    </Card>
  {/if}

  {#if !profile && !loading}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
      <Card>
        <div class="text-center py-6 space-y-3">
          <div class="w-12 h-12 rounded-xl bg-red-500/10 mx-auto flex items-center justify-center">
            <svg class="w-6 h-6 text-red-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0C.488 3.45.029 5.804 0 12c.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0C23.512 20.55 23.971 18.196 24 12c-.029-6.185-.484-8.549-4.385-8.816zM9 16V8l8 4-8 4z"/>
            </svg>
          </div>
          <h3 class="font-semibold">YouTube</h3>
          <p class="text-xs text-white/40">Paste a channel URL like<br/>youtube.com/@channelname</p>
        </div>
      </Card>
      <Card>
        <div class="text-center py-6 space-y-3">
          <div class="w-12 h-12 rounded-xl bg-purple-500/10 mx-auto flex items-center justify-center">
            <svg class="w-6 h-6 text-purple-400" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
            </svg>
          </div>
          <h3 class="font-semibold">TikTok</h3>
          <p class="text-xs text-white/40">Paste a profile URL like<br/>tiktok.com/@username</p>
        </div>
      </Card>
    </div>
  {/if}
</div>
