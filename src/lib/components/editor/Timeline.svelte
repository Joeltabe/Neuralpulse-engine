<script lang="ts">
  import { currentTime, duration, zoom, trimStart, trimEnd, recommendations, sceneBreaks, engagementCurve, timestampAxis, recColor } from '$lib/editor/state'

  let timelineEl: HTMLDivElement
  let svgEl: SVGSVGElement

  let recs: any[] = []
  let sBreaks: any[] = []
  let engCurve: number[] = []
  let timeAxis: number[] = []
  let vidDuration = 0
  let vidTrimStart = 0
  let vidTrimEnd = 0
  let currentZoom = 1

  let subs: (() => void)[] = []

  subs.push(recommendations.subscribe(v => recs = v))
  subs.push(sceneBreaks.subscribe(v => sBreaks = v))
  subs.push(engagementCurve.subscribe(v => engCurve = v))
  subs.push(timestampAxis.subscribe(v => timeAxis = v))
  subs.push(duration.subscribe(v => vidDuration = v))
  subs.push(trimStart.subscribe(v => vidTrimStart = v))
  subs.push(trimEnd.subscribe(v => vidTrimEnd = v))
  subs.push(zoom.subscribe(v => currentZoom = v))

  import { onDestroy } from 'svelte'

  onDestroy(() => subs.forEach(u => u()))

  let dragging: 'trimStart' | 'trimEnd' | null = null

  function seekPixel(clientX: number) {
    if (!svgEl) return
    const rect = svgEl.getBoundingClientRect()
    const x = (clientX - rect.left) / rect.width
    const t = x * vidDuration
    currentTime.set(Math.max(0, Math.min(t, vidDuration)))
  }

  function seek(e: MouseEvent) {
    seekPixel(e.clientX)
  }

  function startDrag(handle: 'trimStart' | 'trimEnd', e: MouseEvent) {
    dragging = handle
    e.stopPropagation()
    e.preventDefault()
  }

  function onPointerMove(e: MouseEvent) {
    if (!dragging) return
    if (!svgEl) return
    const rect = svgEl.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width
    const t = Math.max(0, Math.min(x * vidDuration, vidDuration))
    if (dragging === 'trimStart') trimStart.set(Math.min(t, vidTrimEnd - 0.5))
    else trimEnd.set(Math.max(t, vidTrimStart + 0.5))
  }

  function onPointerUp() {
    dragging = null
  }

  function formatTime(s: number): string {
    if (!isFinite(s) || s < 0) return '0:00'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  let curTime = 0
  currentTime.subscribe(v => curTime = v)

  $effect(() => {
    if (!svgEl) return
    const w = svgEl.clientWidth || 800
    const h = svgEl.clientHeight || 64

    const ctx = svgEl as unknown as SVGSVGElement
    const dur = vidDuration || 1
    let html = ''

    const scaleX = (t: number) => (t / dur) * w

    if (engCurve.length > 1 && timeAxis.length > 1) {
      const pts = engCurve.map((v, i) => {
        const tx = scaleX(timeAxis[i] || (i / engCurve.length) * dur)
        const ty = h - 4 - (v * (h - 12))
        return `${tx},${ty}`
      }).join(' ')
      html += `<polyline points="${pts}" fill="none" stroke="rgba(77,108,245,0.3)" stroke-width="1.5"/>`
    }

    for (const sb of sBreaks) {
      const sx = scaleX(sb.time)
      html += `<line x1="${sx}" y1="0" x2="${sx}" y2="${h}" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="3,3"/>`
    }

    for (const rec of recs) {
      const rx = scaleX(rec.timestamp_sec)
      const style = recColor(rec.severity)
      html += `<circle cx="${rx}" cy="${h / 2}" r="4" fill="${style.glow.replace('0.35', '0.9')}" stroke="rgba(255,255,255,0.3)" stroke-width="0.5"/>`
      html += `<title>${rec.title} at ${formatTime(rec.timestamp_sec)}</title>`
    }

    const curX = scaleX(curTime)
    html += `<line x1="${curX}" y1="0" x2="${curX}" y2="${h}" stroke="rgba(255,255,255,0.8)" stroke-width="2"/>`

    const tsX = scaleX(vidTrimStart)
    const teX = scaleX(vidTrimEnd)
    html += `<rect x="${tsX}" y="0" width="${teX - tsX}" height="${h}" fill="rgba(77,108,245,0.08)" stroke="rgba(77,108,245,0.4)" stroke-width="1" rx="4"/>`

    html += `<rect x="${tsX - 4}" y="2" width="8" height="${h - 4}" fill="rgba(77,108,245,0.6)" rx="2" cursor="ew-resize"/>`
    html += `<rect x="${teX - 4}" y="2" width="8" height="${h - 4}" fill="rgba(77,108,245,0.6)" rx="2" cursor="ew-resize"/>`

    svgEl.innerHTML = html
  })
</script>

<div class="select-none"
  onmousemove={onPointerMove}
  onmouseup={onPointerUp}
  onmouseleave={onPointerUp}
>
  <div class="flex items-center justify-between mb-2">
    <div class="flex items-center gap-2 text-xs text-white/40">
      <span class="font-mono">{formatTime(vidTrimStart)}</span>
      <span class="text-white/20">—</span>
      <span class="font-mono">{formatTime(vidTrimEnd)}</span>
      <span class="text-white/20 ml-2">({formatTime(vidTrimEnd - vidTrimStart)} trimmed)</span>
    </div>
    <div class="flex items-center gap-2">
      <button onclick={() => zoom.set(Math.max(0.5, currentZoom - 0.5))}
        class="w-6 h-6 rounded bg-white/5 hover:bg-white/10 flex items-center justify-center text-xs text-white/50"
      >−</button>
      <div class="w-20 h-1.5 rounded-full bg-white/5 relative">
        <div class="h-full rounded-full bg-neural-500/40" style="width: {(currentZoom / 5) * 100}%"></div>
      </div>
      <button onclick={() => zoom.set(Math.min(5, currentZoom + 0.5))}
        class="w-6 h-6 rounded bg-white/5 hover:bg-white/10 flex items-center justify-center text-xs text-white/50"
      >+</button>
    </div>
  </div>

  <div
    bind:this={timelineEl}
    class="relative w-full bg-white/5 rounded-xl overflow-hidden cursor-pointer"
    style="height: 72px"
    onclick={seek}
  >
    <svg
      bind:this={svgEl}
      class="w-full h-full"
      preserveAspectRatio="none"
    ></svg>

    <div
      class="absolute top-0 bottom-0 w-1 bg-neural-400 shadow-lg shadow-neural-500/50 z-10 pointer-events-none"
      style="left: {(curTime / (vidDuration || 1)) * 100}%"
    ></div>

    <div
      class="absolute top-0 w-3 h-full cursor-ew-resize z-20 group/trim"
      style="left: {(vidTrimStart / (vidDuration || 1)) * 100}%"
      onmousedown={(e) => startDrag('trimStart', e)}
    >
      <div class="w-1 h-full bg-neural-500/60 mx-auto group-hover/trim:bg-neural-400 transition-colors"></div>
    </div>
    <div
      class="absolute top-0 w-3 h-full cursor-ew-resize z-20 group/trim"
      style="left: {(vidTrimEnd / (vidDuration || 1)) * 100}%"
      onmousedown={(e) => startDrag('trimEnd', e)}
    >
      <div class="w-1 h-full bg-neural-500/60 mx-auto group-hover/trim:bg-neural-400 transition-colors"></div>
    </div>
  </div>

  <div class="flex justify-between mt-1 text-[10px] text-white/20 font-mono">
    <span>{formatTime(0)}</span>
    <span>{formatTime(vidDuration / 2)}</span>
    <span>{formatTime(vidDuration)}</span>
  </div>
</div>

<style>
  svg :global(line), svg :global(circle), svg :global(rect), svg :global(polyline) {
    pointer-events: none;
  }
</style>
