<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { currentTime, isPlaying, duration, recommendations, timestampAxis, recColor } from '$lib/editor/state'

  let videoEl: HTMLVideoElement
  let canvasEl: HTMLCanvasElement

  let recs: any[] = []
  let timeAxis: number[] = []
  let vidDuration = 0
  let subs: (() => void)[] = []

  subs.push(recommendations.subscribe(v => recs = v))
  subs.push(timestampAxis.subscribe(v => timeAxis = v))
  subs.push(duration.subscribe(v => vidDuration = v))

  function formatTime(s: number): string {
    if (!isFinite(s) || s < 0) return '0:00'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  let seekHover = $state(false)

  onMount(() => {
    const v = videoEl
    v.addEventListener('timeupdate', () => currentTime.set(v.currentTime))
    v.addEventListener('play', () => isPlaying.set(true))
    v.addEventListener('pause', () => isPlaying.set(false))
    v.addEventListener('loadedmetadata', () => {
      duration.set(v.duration || 0)
    })
    animLoop()
  })

  onDestroy(() => {
    subs.forEach(u => u())
    if (animId) cancelAnimationFrame(animId)
  })

  let animId = 0

  function animLoop() {
    animId = requestAnimationFrame(animLoop)
    if (!canvasEl || !videoEl) return
    const w = videoEl.clientWidth
    const h = videoEl.clientHeight
    if (canvasEl.width !== w || canvasEl.height !== h) {
      canvasEl.width = w
      canvasEl.height = h
    }
    const ctx = canvasEl.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, w, h)

    const ct = videoEl.currentTime
    const dur = vidDuration || 1

    for (const rec of recs) {
      const rx = (rec.timestamp_sec / dur) * w
      const style = recColor(rec.severity)
      const pulse = 0.6 + 0.4 * Math.sin(Date.now() / 400 + rec.timestamp_sec)
      ctx.fillStyle = style.glow.replace('0.35', String(pulse * 0.35))
      ctx.fillRect(rx - 1, 0, 3, h)
    }

    const nearRecs = recs.filter(r => Math.abs(r.timestamp_sec - ct) < 3)
    for (const rec of nearRecs) {
      const rx = (rec.timestamp_sec / dur) * w
      const style = recColor(rec.severity)
      const radius = 18 + 6 * Math.sin(Date.now() / 300 + rec.timestamp_sec)
      const grad = ctx.createRadialGradient(rx, h / 2, 0, rx, h / 2, radius)
      grad.addColorStop(0, style.glow)
      grad.addColorStop(1, 'transparent')
      ctx.fillStyle = grad
      ctx.beginPath()
      ctx.arc(rx, h / 2, radius, 0, Math.PI * 2)
      ctx.fill()
    }
  }

  function togglePlay() {
    if (!videoEl) return
    if (videoEl.paused) videoEl.play()
    else videoEl.pause()
  }

  function seekClient(clientX: number) {
    if (!videoEl) return
    const rect = videoEl.getBoundingClientRect()
    const x = (clientX - rect.left) / rect.width
    videoEl.currentTime = Math.max(0, Math.min(x * videoEl.duration, videoEl.duration))
  }
</script>

<div class="relative w-full aspect-video bg-black rounded-2xl overflow-hidden group">
  <video
    bind:this={videoEl}
    class="w-full h-full object-contain"
    playsinline
    preload="metadata"
  ></video>
  <canvas
    bind:this={canvasEl}
    class="absolute inset-0 w-full h-full pointer-events-none z-10"
  ></canvas>

  <div
    class="absolute inset-0 z-20 cursor-pointer"
    onmousemove={(e) => { seekHover = true }}
    onmouseleave={() => { seekHover = false }}
    onclick={(e) => seekClient(e.clientX)}
    onmouseenter={() => { seekHover = true }}
  ></div>

  <div class="absolute bottom-0 left-0 right-0 z-30 p-4 bg-gradient-to-t from-black/80 via-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300">
    <div class="flex items-center gap-3">
      <button onclick={togglePlay}
        class="w-9 h-9 rounded-full bg-white/10 backdrop-blur-md flex items-center justify-center hover:bg-white/20 transition-colors flex-shrink-0"
      >
        {#if videoEl?.paused !== false}
          <svg class="w-4 h-4 text-white ml-0.5" fill="currentColor" viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
        {:else}
          <svg class="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/></svg>
        {/if}
      </button>
      <div class="text-xs text-white/70 font-mono">
        {formatTime(videoEl?.currentTime || 0)} / {formatTime(vidDuration)}
      </div>
    </div>
  </div>
</div>
