<script lang="ts">
  import { isExporting, exportProgress, ffmpegLoaded, duration, trimStart, trimEnd, cuts, videoFile } from '$lib/editor/state'
  import { loadFFmpeg, exportVideo } from '$lib/editor/ffmpeg'

  let subs: (() => void)[] = []
  let isExp = false
  let progress = 0
  let ffLoaded = false
  let vidFile: File | null = null
  let vidDuration = 0
  let vidTrimStart = 0
  let vidTrimEnd = 0
  let editorCuts: any[] = []

  subs.push(isExporting.subscribe(v => isExp = v))
  subs.push(exportProgress.subscribe(v => progress = v))
  subs.push(ffmpegLoaded.subscribe(v => ffLoaded = v))
  subs.push(videoFile.subscribe(v => vidFile = v))
  subs.push(duration.subscribe(v => vidDuration = v))
  subs.push(trimStart.subscribe(v => vidTrimStart = v))
  subs.push(trimEnd.subscribe(v => vidTrimEnd = v))
  subs.push(cuts.subscribe(v => editorCuts = v))

  import { onDestroy } from 'svelte'
  onDestroy(() => subs.forEach(u => u()))

  let show = $state(false)

  async function handleExport() {
    if (!vidFile) return
    isExporting.set(true)
    show = false

    try {
      if (!ffLoaded) {
        await loadFFmpeg()
        ffmpegLoaded.set(true)
      }

      const blob = await exportVideo(
        vidFile,
        vidTrimStart,
        vidTrimEnd,
        editorCuts,
        (p: number) => exportProgress.set(p),
      )

      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `neural-optimized-${vidFile.name}`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Export failed:', err)
    } finally {
      isExporting.set(false)
      exportProgress.set(0)
    }
  }

  async function initFFmpeg() {
    if (!ffLoaded) {
      await loadFFmpeg()
      ffmpegLoaded.set(true)
    }
    show = true
  }

  function formatTime(s: number): string {
    if (!isFinite(s) || s < 0) return '0:00'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }
</script>

<button
  onclick={initFFmpeg}
  disabled={isExp || !vidFile}
  class={"px-6 py-2.5 rounded-xl font-semibold text-sm transition-all duration-300 flex items-center gap-2 " + (isExp || !vidFile ? 'bg-neural-500/30 text-white/30 cursor-not-allowed' : 'bg-neural-500 hover:bg-neural-400 text-white')}
>
  {#if isExp}
    <svg class="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" stroke-dasharray="31.4 31.4" stroke-linecap="round"/></svg>
    Exporting {progress}%
  {:else}
    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    Export Video
  {/if}
</button>

{#if show}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => show = false}>
    <div class="glass-strong rounded-2xl p-6 max-w-md w-full mx-4" onclick={(e) => e.stopPropagation()}>
      <h3 class="text-lg font-semibold mb-4">Export Video</h3>

      <div class="space-y-3 mb-6">
        <div class="flex justify-between text-sm">
          <span class="text-white/50">Duration</span>
          <span class="font-mono">{formatTime(vidTrimEnd - vidTrimStart)}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-white/50">Trim range</span>
          <span class="font-mono">{formatTime(vidTrimStart)} — {formatTime(vidTrimEnd)}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-white/50">Cuts applied</span>
          <span class="font-mono">{editorCuts.filter(c => c.enabled).length}</span>
        </div>
        <div class="flex justify-between text-sm">
          <span class="text-white/50">Format</span>
          <span class="font-mono">MP4 (H.264)</span>
        </div>
      </div>

      <div class="flex gap-3">
        <button onclick={() => show = false}
          class="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium bg-white/5 hover:bg-white/10 transition-colors"
        >Cancel</button>
        <button onclick={handleExport}
          class="flex-1 px-4 py-2.5 rounded-xl text-sm font-semibold bg-neural-500 hover:bg-neural-400 transition-colors"
        >Export</button>
      </div>
    </div>
  </div>
{/if}
