<script lang="ts">
  import { onMount } from 'svelte'
  import { page } from '$app/stores'
  import { goto } from '$app/navigation'
  import { videoSrc, videoFile, duration, trimEnd, recommendations, sceneBreaks, engagementCurve, timestampAxis, cuts, resetEditor } from '$lib/editor/state'
  import VideoPreview from '$lib/components/editor/VideoPreview.svelte'
  import Timeline from '$lib/components/editor/Timeline.svelte'
  import RecommendationsPanel from '$lib/components/editor/RecommendationsPanel.svelte'
  import ExportDialog from '$lib/components/editor/ExportDialog.svelte'
  import type { AnalysisResponse } from '$lib/types/api'
  import TranscriptEditor from '$lib/components/editor/TranscriptEditor.svelte'
  import { transcriptSegments, wordLevelScores } from '$lib/editor/state'

  let loading = $state(true)
  let error = $state('')
  let title = $state('Video Editor')
  let activeTab = $state<'recommendations' | 'cuts' | 'transcript'>('recommendations')

  let currentRecs: any[] = []
  recommendations.subscribe(v => currentRecs = v)
  let currentTranscripts: any[] = []
  transcriptSegments.subscribe(v => currentTranscripts = v)
  let transcriptCount = $state(0)
  transcriptSegments.subscribe(v => transcriptCount = v.length)

  onMount(async () => {
    const params = $page.url.searchParams
    const idParam = params.get('id')
    const urlParam = params.get('url')

    if (idParam) {
      try {
        const res = await fetch('/api/history/analyses')
        const data = await res.json()
        if (data.success) {
          const found = data.analyses.find((a: any) => a.id === idParam)
          if (found?.results) {
            await loadFromResult(found.results)
          } else {
            error = 'Analysis result not found'
          }
        } else {
          error = 'Failed to load analysis'
        }
      } catch (e) {
        error = 'Failed to fetch analysis data'
      }
      loading = false
    } else if (urlParam) {
      videoSrc.set(urlParam)
      const file = await fetchAsFile(urlParam)
      if (file) videoFile.set(file)
      loading = false
    } else {
      error = 'No video or analysis data provided. Please analyze a video first.'
      loading = false
    }
  })

  async function fetchAsFile(url: string): Promise<File | null> {
    try {
      const resp = await fetch(url)
      const blob = await resp.blob()
      const name = url.split('/').pop() || 'video.mp4'
      return new File([blob], name, { type: blob.type || 'video/mp4' })
    } catch {
      return null
    }
  }

  async function loadFromResult(result: any) {
    title = `Editing: ${result.filename || 'Untitled'}`
    if (result.id && result.media_type === 'video') {
      const vidUrl = `/api/analyze/video/file/${result.id}`
      videoSrc.set(vidUrl)
      const file = await fetchAsFile(vidUrl)
      if (file) videoFile.set(file)
    }

    duration.set(result.duration_sec || 0)
    trimEnd.set(result.duration_sec || 0)
    engagementCurve.set(result.engagement_curve || [])
    timestampAxis.set(result.timestamp_axis || [])
    recommendations.set(result.recommendations || [])
    transcriptSegments.set(result.transcript_segments || [])
    wordLevelScores.set(result.word_level_scores || [])

    const breaks: any[] = (result.scene_breaks || []).map((t: number) => ({
      time: t,
      transition: 'fade' as const,
      auto_applied: false,
    }))
    sceneBreaks.set(breaks)

    loading = false
  }

  function goBack() {
    goto('/dashboard')
  }

  let vidSrc = ''
  videoSrc.subscribe(v => vidSrc = v)
</script>

<div class="min-h-screen bg-surface-950 text-white">
  <!-- Top Bar -->
  <header class="flex items-center justify-between px-6 py-3 border-b border-white/5">
    <div class="flex items-center gap-4">
      <button onclick={goBack}
        class="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 flex items-center justify-center transition-colors"
      >
        <svg class="w-4 h-4 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"/></svg>
      </button>
      <h1 class="text-sm font-semibold truncate max-w-sm">{title}</h1>
    </div>
    <div class="flex items-center gap-3">
      <ExportDialog />
    </div>
  </header>

  {#if loading}
    <div class="flex items-center justify-center h-[80vh]">
      <div class="text-center">
        <div class="w-8 h-8 border-2 border-neural-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
        <p class="text-sm text-white/40">Loading editor...</p>
      </div>
    </div>
  {:else if error}
    <div class="flex items-center justify-center h-[80vh]">
      <div class="text-center max-w-md">
        <div class="w-16 h-16 rounded-2xl bg-red-500/10 flex items-center justify-center mx-auto mb-4">
          <svg class="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z"/></svg>
        </div>
        <p class="text-white/60">{error}</p>
        <button onclick={goBack} class="mt-4 px-4 py-2 rounded-xl bg-neural-500/20 text-neural-400 text-sm hover:bg-neural-500/30 transition-colors">
          Back to Dashboard
        </button>
      </div>
    </div>
  {:else}
    <div class="flex h-[calc(100vh-57px)]">
      <!-- Main Area -->
      <div class="flex-1 flex flex-col min-w-0">
        <div class="flex-1 p-4 flex items-center justify-center bg-black/40">
          <div class="w-full max-w-4xl">
            <VideoPreview />
          </div>
        </div>
        <div class="p-4 pt-2 border-t border-white/5">
          <Timeline />
        </div>
      </div>

      <!-- Side Panel -->
      <div class="w-80 border-l border-white/5 flex flex-col bg-surface-950/80">
        <div class="flex border-b border-white/5">
          <button
            onclick={() => activeTab = 'recommendations'}
            class="flex-1 py-2.5 text-xs font-medium transition-colors {activeTab === 'recommendations' ? 'text-white/80 border-b-2 border-neural-500' : 'text-white/30 border-b-2 border-b-transparent'}"
          >
            Recommendations ({currentRecs.length})
          </button>
          <button
            onclick={() => activeTab = 'cuts'}
            class="flex-1 py-2.5 text-xs font-medium transition-colors {activeTab === 'cuts' ? 'text-white/80 border-b-2 border-neural-500' : 'text-white/30 border-b-2 border-b-transparent'}"
          >
            Cuts & Edits
          </button>
          <button
            onclick={() => activeTab = 'transcript'}
            class="flex-1 py-2.5 text-xs font-medium transition-colors {activeTab === 'transcript' ? 'text-white/80 border-b-2 border-neural-500' : 'text-white/30 border-b-2 border-b-transparent'}"
          >
            Transcript ({currentTranscripts.length})
          </button>
        </div>

        <div class="flex-1 overflow-hidden">
          {#if activeTab === 'recommendations'}
            <RecommendationsPanel />
          {:else if activeTab === 'cuts'}
            <div class="p-4 space-y-2">
              {#each $cuts as cut, i}
                <label class="flex items-center gap-3 p-3 rounded-xl bg-white/[0.02] hover:bg-white/5 transition-colors cursor-pointer">
                  <input type="checkbox" bind:checked={cut.enabled} class="rounded bg-white/5 border-white/10 text-neural-500 focus:ring-neural-500" />
                  <div class="flex-1 min-w-0">
                    <p class="text-sm font-medium">{(cut.time).toFixed(1)}s {cut.type}</p>
                    <p class="text-xs text-white/40">Cut at marker position</p>
                  </div>
                </label>
              {:else}
                <p class="text-sm text-white/30 text-center py-8">No cuts defined yet. Recommendations will suggest cut points automatically.</p>
              {/each}
            </div>
          {:else}
            <TranscriptEditor />
          {/if}
        </div>
      </div>
    </div>
  {/if}
</div>

{#if vidSrc}
  <video src={vidSrc} preload="metadata" style="display:none"></video>
{/if}
