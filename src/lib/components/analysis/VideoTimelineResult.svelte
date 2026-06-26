<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { recColor } from '$lib/editor/state'
  import type { Recommendation } from '$lib/types/api'

  let { analysisId = '', recommendations = [] as Recommendation[], engagementCurve = [] as number[], timestampAxis = [] as number[], sceneBreaks = [] as number[] } = $props()

  let videoEl: HTMLVideoElement
  let canvasEl: HTMLCanvasElement
  let timelineSvg: SVGSVGElement
  let videoUrl = $state('')
  let currentTime = $state(0)
  let duration = $state(0)
  let isPlaying = $state(false)

  onMount(() => {
    videoUrl = `/api/analyze/video/file/${analysisId}`

    const v = videoEl
    if (!v) return
    v.addEventListener('timeupdate', () => { currentTime = v.currentTime })
    v.addEventListener('play', () => { isPlaying = true })
    v.addEventListener('pause', () => { isPlaying = false })
    v.addEventListener('loadedmetadata', () => { duration = v.duration || 0 })
    animLoop()
  })

  onDestroy(() => { if (animId) cancelAnimationFrame(animId) })

  let animId = 0
  function animLoop() {
    animId = requestAnimationFrame(animLoop)
    if (!canvasEl || !videoEl) return
    const w = videoEl.clientWidth, h = videoEl.clientHeight
    if (canvasEl.width !== w || canvasEl.height !== h) { canvasEl.width = w; canvasEl.height = h }
    const ctx = canvasEl.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, w, h)
    const dur = duration || 1

    for (const rec of recommendations) {
      const rx = (rec.timestamp_sec / dur) * w
      const style = recColor(rec.severity)
      const pulse = 0.6 + 0.4 * Math.sin(Date.now() / 400 + rec.timestamp_sec)
      ctx.fillStyle = style.glow.replace('0.35', String(pulse * 0.35))
      ctx.fillRect(rx - 1, 0, 3, h)
    }

    const near = recommendations.filter(r => Math.abs(r.timestamp_sec - currentTime) < 3)
    for (const rec of near) {
      const rx = (rec.timestamp_sec / dur) * w
      const style = recColor(rec.severity)
      const radius = 18 + 6 * Math.sin(Date.now() / 300 + rec.timestamp_sec)
      const grad = ctx.createRadialGradient(rx, h / 2, 0, rx, h / 2, radius)
      grad.addColorStop(0, style.glow); grad.addColorStop(1, 'transparent')
      ctx.fillStyle = grad; ctx.beginPath(); ctx.arc(rx, h / 2, radius, 0, Math.PI * 2); ctx.fill()
    }
  }

  function togglePlay() {
    if (!videoEl) return
    if (videoEl.paused) videoEl.play()
    else videoEl.pause()
  }

  function seekTo(time: number) { if (videoEl && duration) videoEl.currentTime = Math.max(0, Math.min(time, duration)) }

  function formatTime(s: number): string {
    if (!isFinite(s) || s < 0) return '0:00'
    const m = Math.floor(s / 60); const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  // Timeline SVG
  $effect(() => {
    if (!timelineSvg || !duration) return
    const w = timelineSvg.clientWidth || 800
    const h = timelineSvg.clientHeight || 48
    const scaleX = (t: number) => (t / duration) * w

    let html = ''
    if (engagementCurve.length > 1 && timestampAxis.length > 1) {
      const pts = engagementCurve.map((v, i) => {
        const tx = scaleX(timestampAxis[i] || (i / engagementCurve.length) * duration)
        const ty = h - 4 - (v * (h - 8))
        return `${tx},${ty}`
      }).join(' ')
      html += `<polyline points="${pts}" fill="none" stroke="rgba(77,108,245,0.25)" stroke-width="1.5"/>`
    }

    for (const sb of sceneBreaks) {
      const sx = scaleX(sb)
      html += `<line x1="${sx}" y1="0" x2="${sx}" y2="${h}" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="3,3"/>`
    }

    for (const rec of recommendations) {
      const rx = scaleX(rec.timestamp_sec)
      const style = recColor(rec.severity)
      html += `<circle cx="${rx}" cy="${h / 2}" r="3" fill="${style.glow.replace('0.35', '0.9')}" stroke="rgba(255,255,255,0.3)" stroke-width="0.5"/>`
      html += `<title>${rec.title} at ${formatTime(rec.timestamp_sec)}</title>`
    }

    const curX = scaleX(currentTime)
    html += `<line x1="${curX}" y1="0" x2="${curX}" y2="${h}" stroke="rgba(255,255,255,0.7)" stroke-width="2"/>`

    timelineSvg.innerHTML = html
  })
</script>

<div class="space-y-3">
  <!-- Video Player -->
  <div class="relative w-full aspect-video bg-black rounded-2xl overflow-hidden group">
    <video bind:this={videoEl} src={videoUrl} class="w-full h-full object-contain" playsinline preload="metadata"></video>
    <canvas bind:this={canvasEl} class="absolute inset-0 w-full h-full pointer-events-none z-10"></canvas>

    <div class="absolute inset-0 z-20 cursor-pointer" onclick={(e) => {
      if (!videoEl) return
      const rect = videoEl.getBoundingClientRect()
      const x = (e.clientX - rect.left) / rect.width
      videoEl.currentTime = x * (videoEl.duration || 0)
    }}></div>

    <div class="absolute bottom-0 left-0 right-0 z-30 p-4 bg-gradient-to-t from-black/80 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
      <div class="flex items-center gap-3">
        <button onclick={togglePlay}
          class="w-9 h-9 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center hover:bg-white/20 transition-colors"
        >
          {#if !isPlaying}
            <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
          {:else}
            <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
          {/if}
        </button>
        <span class="text-xs text-white/70 font-mono">{formatTime(currentTime)} / {formatTime(duration)}</span>
      </div>
    </div>
  </div>

  <!-- Timeline with markers -->
  <div class="bg-white/[0.03] rounded-xl p-3">
    <svg bind:this={timelineSvg} class="w-full h-12 cursor-pointer" preserveAspectRatio="none"
      onclick={(e) => {
        if (!timelineSvg || !duration) return
        const rect = timelineSvg.getBoundingClientRect()
        const x = (e.clientX - rect.left) / rect.width
        seekTo(x * duration)
      }}
    ></svg>

    <!-- Recommendation chips -->
    <div class="flex flex-wrap gap-1.5 mt-2">
      {#each recommendations as rec}
        <button onclick={() => seekTo(rec.timestamp_sec)}
          class="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-colors {rec.severity === 'critical' ? 'bg-red-500/10 text-red-300 hover:bg-red-500/20' : rec.severity === 'moderate' ? 'bg-amber-500/10 text-amber-300 hover:bg-amber-500/20' : 'bg-blue-500/10 text-blue-300 hover:bg-blue-500/20'}"
        >
          <span class="w-1.5 h-1.5 rounded-full {rec.severity === 'critical' ? 'bg-red-400' : rec.severity === 'moderate' ? 'bg-amber-400' : 'bg-blue-400'}"></span>
          {formatTime(rec.timestamp_sec)}s — {rec.title}
        </button>
      {/each}
    </div>
  </div>
</div>