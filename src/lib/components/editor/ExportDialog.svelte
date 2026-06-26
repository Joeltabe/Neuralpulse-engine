<script lang="ts">
  import { isExporting, exportProgress, ffmpegLoaded, duration, trimStart, trimEnd, cuts, videoFile } from '$lib/editor/state'
  import { loadFFmpeg, exportVideo, type ExportOptions } from '$lib/editor/ffmpeg'

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

  let format = $state<ExportOptions['format']>('mp4')
  let resolution = $state<ExportOptions['resolution']>('source')
  let quality = $state<ExportOptions['quality']>('medium')
  let preset = $state('fast')

  const PRESETS: Record<string, Partial<ExportOptions>> = {
    'high-quality': { quality: 'high', preset: 'slow', resolution: 'source' },
    'small-file': { quality: 'low', preset: 'fast', resolution: '720p' },
    youtube: { quality: 'high', preset: 'medium', resolution: '1080p' },
    social: { quality: 'medium', preset: 'fast', resolution: '720p' },
  }

  function applyPreset(name: string) {
    const p = PRESETS[name]
    if (!p) return
    if (p.quality) quality = p.quality
    if (p.preset) preset = p.preset
    if (p.resolution) resolution = p.resolution
  }

  let estimatedSize = $derived.by(() => {
    const dur = vidTrimEnd - vidTrimStart
    if (dur <= 0) return '—'
    const qualityFactors: Record<string, number> = { high: 1.5, medium: 1.0, low: 0.5 }
    const resolutionFactors: Record<string, number> = { source: 1.0, '1080p': 1.0, '720p': 0.5, '480p': 0.3 }
    const formatFactors: Record<string, number> = { mp4: 1.0, webm: 0.9, gif: 0.3 }
    const mbPerSec = 0.5 * (qualityFactors[quality] || 1) * (resolutionFactors[resolution] || 1) * (formatFactors[format] || 1)
    const mb = dur * mbPerSec
    if (mb < 1) return `${Math.round(mb * 1000)} KB`
    return `${mb.toFixed(1)} MB`
  })

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
        { format, resolution, quality, preset },
        (p: number) => exportProgress.set(p),
      )

      const ext = format === 'webm' ? 'webm' : format === 'gif' ? 'gif' : 'mp4'
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      const baseName = vidFile.name.replace(/\.[^.]+$/, '')
      a.href = url
      a.download = `neural-optimized-${baseName}.${ext}`
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
    Export
  {/if}
</button>

{#if show}
  <div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm" onclick={() => show = false}>
    <div class="glass-strong rounded-2xl p-6 max-w-lg w-full mx-4" onclick={(e) => e.stopPropagation()}>
      <h3 class="text-lg font-semibold mb-4">Export Video</h3>

      <!-- Presets -->
      <div class="mb-4">
        <p class="text-xs text-white/40 mb-2">Quick presets</p>
        <div class="grid grid-cols-4 gap-2">
          <button onclick={() => applyPreset('high-quality')}
            class="py-2 px-2 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/60 hover:text-white/80 transition-colors text-center leading-tight">High<br/>Quality</button>
          <button onclick={() => applyPreset('small-file')}
            class="py-2 px-2 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/60 hover:text-white/80 transition-colors text-center leading-tight">Small<br/>File</button>
          <button onclick={() => applyPreset('youtube')}
            class="py-2 px-2 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/60 hover:text-white/80 transition-colors text-center leading-tight">YouTube</button>
          <button onclick={() => applyPreset('social')}
            class="py-2 px-2 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/60 hover:text-white/80 transition-colors text-center leading-tight">Social<br/>Media</button>
        </div>
      </div>

      <!-- Format selection -->
      <div class="space-y-3 mb-6">
        <div>
          <p class="text-xs text-white/40 mb-1.5">Format</p>
          <div class="flex gap-2">
            {#each ['mp4', 'webm', 'gif'] as fmt}
              <button
                onclick={() => format = fmt as ExportOptions['format']}
                class={"flex-1 py-2 rounded-lg text-xs font-medium transition-colors " + (format === fmt ? 'bg-neural-500/20 text-neural-400 border border-neural-500/30' : 'bg-white/5 text-white/50 hover:bg-white/10 border border-transparent')}
              >{fmt.toUpperCase()}</button>
            {/each}
          </div>
        </div>

        <div>
          <p class="text-xs text-white/40 mb-1.5">Resolution</p>
          <div class="flex gap-2">
            {#each [{ value: 'source', label: 'Source' }, { value: '1080p', label: '1080p' }, { value: '720p', label: '720p' }, { value: '480p', label: '480p' }] as res}
              <button
                onclick={() => resolution = res.value as ExportOptions['resolution']}
                class={"flex-1 py-2 rounded-lg text-xs font-medium transition-colors " + (resolution === res.value ? 'bg-neural-500/20 text-neural-400 border border-neural-500/30' : 'bg-white/5 text-white/50 hover:bg-white/10 border border-transparent')}
              >{res.label}</button>
            {/each}
          </div>
        </div>

        <div>
          <p class="text-xs text-white/40 mb-1.5">Quality</p>
          <div class="flex gap-2">
            {#each [{ value: 'high', label: 'High' }, { value: 'medium', label: 'Medium' }, { value: 'low', label: 'Low' }] as q}
              <button
                onclick={() => quality = q.value as ExportOptions['quality']}
                class={"flex-1 py-2 rounded-lg text-xs font-medium transition-colors " + (quality === q.value ? 'bg-neural-500/20 text-neural-400 border border-neural-500/30' : 'bg-white/5 text-white/50 hover:bg-white/10 border border-transparent')}
              >{q.label}</button>
            {/each}
          </div>
        </div>

        <div class="border-t border-white/5 pt-3 space-y-2">
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
            <span class="text-white/50">Est. size</span>
            <span class="font-mono">{estimatedSize}</span>
          </div>
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