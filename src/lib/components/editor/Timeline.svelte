<script lang="ts">
  import { currentTime, duration, zoom, trimStart, trimEnd, recommendations, sceneBreaks, engagementCurve, timestampAxis, recColor, visibleRange } from '$lib/editor/state'

  let timelineEl: HTMLDivElement
  let svgEl: SVGSVGElement
  let scrollContainer: HTMLDivElement

  let recs: any[] = []
  let sBreaks: any[] = []
  let engCurve: number[] = []
  let timeAxis: number[] = []
  let vidDuration = 0
  let vidTrimStart = 0
  let vidTrimEnd = 0
  let currentZoom = 1
  let vRange = { start: 0, end: 0 }

  let subs: (() => void)[] = []

  subs.push(recommendations.subscribe(v => recs = v))
  subs.push(sceneBreaks.subscribe(v => sBreaks = v))
  subs.push(engagementCurve.subscribe(v => engCurve = v))
  subs.push(timestampAxis.subscribe(v => timeAxis = v))
  subs.push(duration.subscribe(v => vidDuration = v))
  subs.push(trimStart.subscribe(v => vidTrimStart = v))
  subs.push(trimEnd.subscribe(v => vidTrimEnd = v))
  subs.push(zoom.subscribe(v => currentZoom = v))
  subs.push(visibleRange.subscribe(v => vRange = v))

  import { onDestroy } from 'svelte'

  onDestroy(() => subs.forEach(u => u()))

  let dragging: 'trimStart' | 'trimEnd' | 'timeline' | null = null
  let dragStartX = 0
  let dragStartRange = { start: 0, end: 0 }

  function viewScaleX(t: number, w: number) {
    const range = vRange.end - vRange.start
    return ((t - vRange.start) / range) * w
  }

  function viewTimeFromX(clientX: number) {
    if (!svgEl) return 0
    const rect = svgEl.getBoundingClientRect()
    const x = (clientX - rect.left) / rect.width
    const range = vRange.end - vRange.start
    return vRange.start + x * range
  }

  function seek(e: MouseEvent) {
    if (dragging) return
    const t = viewTimeFromX(e.clientX)
    currentTime.set(Math.max(0, Math.min(t, vidDuration)))
  }

  function startDrag(handle: 'trimStart' | 'trimEnd', e: MouseEvent) {
    dragging = handle
    dragStartX = e.clientX
    e.stopPropagation(); e.preventDefault()
  }

  function startPan(e: MouseEvent) {
    if (e.button !== 0) return
    dragging = 'timeline'
    dragStartX = e.clientX
    dragStartRange = { ...vRange }
    e.stopPropagation(); e.preventDefault()
  }

  function onPointerMove(e: MouseEvent) {
    if (!svgEl) return
    const rect = svgEl.getBoundingClientRect()
    const range = vRange.end - vRange.start

    if (dragging === 'trimStart') {
      const t = Math.max(0, Math.min(viewTimeFromX(e.clientX), vidTrimEnd - 0.5))
      trimStart.set(t)
    } else if (dragging === 'trimEnd') {
      const t = Math.max(vidTrimStart + 0.5, Math.min(viewTimeFromX(e.clientX), vidDuration))
      trimEnd.set(t)
    } else if (dragging === 'timeline') {
      const dx = (e.clientX - dragStartX) / rect.width * range
      const newStart = Math.max(0, Math.min(dragStartRange.start - dx, vidDuration - range))
      const newEnd = newStart + range
      if (newEnd <= vidDuration && newStart >= 0) {
        zoom.set(vidDuration / range)
      }
    }
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

  function getTimeMarkers(): number[] {
    const range = vRange.end - vRange.start
    let interval = 30
    if (range <= 10) interval = 1
    else if (range <= 30) interval = 5
    else if (range <= 60) interval = 10
    else if (range <= 300) interval = 30
    else if (range <= 600) interval = 60

    const markers: number[] = []
    const start = Math.floor(vRange.start / interval) * interval
    let t = start
    while (t <= vRange.end) {
      if (t >= vRange.start) markers.push(t)
      t += interval
    }
    return markers
  }

  $effect(() => {
    if (!svgEl) return
    const w = svgEl.clientWidth || 800
    const h = svgEl.clientHeight || 64
    const range = vRange.end - vRange.start
    if (range <= 0) return

    const ctx = svgEl as unknown as SVGSVGElement
    let html = ''

    const scaleX = (t: number) => viewScaleX(t, w)

    if (engCurve.length > 1 && timeAxis.length > 1) {
      const pts = engCurve.map((v, i) => {
        const tx = scaleX(timeAxis[i] || (i / engCurve.length) * vidDuration)
        const ty = h - 4 - (v * (h - 12))
        return `${tx},${ty}`
      }).join(' ')
      html += `<polyline points="${pts}" fill="none" stroke="rgba(77,108,245,0.3)" stroke-width="1.5"/>`
    }

    for (const sb of sBreaks) {
      if (sb.time < vRange.start || sb.time > vRange.end) continue
      const sx = scaleX(sb.time)
      html += `<line x1="${sx}" y1="0" x2="${sx}" y2="${h}" stroke="rgba(255,255,255,0.08)" stroke-width="1" stroke-dasharray="3,3"/>`
    }

    for (const rec of recs) {
      if (rec.timestamp_sec < vRange.start || rec.timestamp_sec > vRange.end) continue
      const rx = scaleX(rec.timestamp_sec)
      const style = recColor(rec.severity)
      html += `<circle cx="${rx}" cy="${h / 2}" r="4" fill="${style.glow.replace('0.35', '0.9')}" stroke="rgba(255,255,255,0.3)" stroke-width="0.5"/>`
      html += `<title>${rec.title} at ${formatTime(rec.timestamp_sec)}</title>`
    }

    const curX = scaleX(curTime)
    if (curTime >= vRange.start && curTime <= vRange.end) {
      html += `<line x1="${curX}" y1="0" x2="${curX}" y2="${h}" stroke="rgba(255,255,255,0.8)" stroke-width="2"/>`
    }

    const tsX = scaleX(Math.max(vidTrimStart, vRange.start))
    const teX = scaleX(Math.min(vidTrimEnd, vRange.end))
    const trimVisible = vidTrimStart < vRange.end && vidTrimEnd > vRange.start
    if (trimVisible) {
      html += `<rect x="${tsX}" y="0" width="${Math.max(0, teX - tsX)}" height="${h}" fill="rgba(77,108,245,0.08)" stroke="rgba(77,108,245,0.4)" stroke-width="1" rx="4"/>`

      if (vidTrimStart >= vRange.start && vidTrimStart <= vRange.end) {
        html += `<rect x="${tsX - 4}" y="2" width="8" height="${h - 4}" fill="rgba(77,108,245,0.6)" rx="2" cursor="ew-resize"/>`
      }
      if (vidTrimEnd >= vRange.start && vidTrimEnd <= vRange.end) {
        html += `<rect x="${teX - 4}" y="2" width="8" height="${h - 4}" fill="rgba(77,108,245,0.6)" rx="2" cursor="ew-resize"/>`
      }
    }

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
      <button onclick={() => zoom.set(1)}
        class="w-6 h-6 rounded bg-white/5 hover:bg-white/10 flex items-center justify-center text-xs text-white/50 ml-1"
        title="Reset zoom"
      >⟲</button>
    </div>
  </div>

  <div class="relative">
    <div class="relative w-full bg-white/5 rounded-xl overflow-hidden"
      style="height: 72px"
    >
      <!-- Time ruler -->
      <div class="absolute top-0 left-0 right-0 h-4 z-10 pointer-events-none">
        {#each getTimeMarkers() as marker}
          <div
            class="absolute top-0 text-[8px] text-white/20 font-mono"
            style="left: {viewScaleX(marker, 100)}%"
          >
            <span class="inline-block -translate-x-1/2">{formatTime(marker)}</span>
          </div>
        {/each}
      </div>

      <svg
        bind:this={svgEl}
        class="w-full h-full cursor-pointer"
        preserveAspectRatio="none"
        onmousedown={startPan}
        onclick={seek}
      ></svg>

      <div
        class="absolute top-0 bottom-0 w-1 bg-neural-400 shadow-lg shadow-neural-500/50 z-10 pointer-events-none"
        style="left: {((curTime - vRange.start) / Math.max(vRange.end - vRange.start, 0.1)) * 100}%; display: {curTime >= vRange.start && curTime <= vRange.end ? 'block' : 'none'}"
      ></div>

      {#if vidTrimStart >= vRange.start && vidTrimStart <= vRange.end}
        <div
          class="absolute top-0 w-3 h-full cursor-ew-resize z-20 group/trim"
          style="left: {((vidTrimStart - vRange.start) / Math.max(vRange.end - vRange.start, 0.1)) * 100}%"
          onmousedown={(e) => startDrag('trimStart', e)}
        >
          <div class="w-1 h-full bg-neural-500/60 mx-auto group-hover/trim:bg-neural-400 transition-colors"></div>
        </div>
      {/if}
      {#if vidTrimEnd >= vRange.start && vidTrimEnd <= vRange.end}
        <div
          class="absolute top-0 w-3 h-full cursor-ew-resize z-20 group/trim"
          style="left: {((vidTrimEnd - vRange.start) / Math.max(vRange.end - vRange.start, 0.1)) * 100}%"
          onmousedown={(e) => startDrag('trimEnd', e)}
        >
          <div class="w-1 h-full bg-neural-500/60 mx-auto group-hover/trim:bg-neural-400 transition-colors"></div>
        </div>
      {/if}
    </div>

    <!-- Mini-map overview -->
    <div class="mt-1.5 h-4 bg-white/5 rounded-lg overflow-hidden relative cursor-pointer"
      onclick={(e) => {
        const rect = e.currentTarget.getBoundingClientRect()
        const x = (e.clientX - rect.left) / rect.width
        const t = x * vidDuration
        zoom.set(1)
        currentTime.set(t)
      }}
    >
      <div
        class="absolute top-0 h-full bg-neural-500/20 border-l border-r border-neural-500/40"
        style="left: {(vRange.start / vidDuration) * 100}%; width: {((vRange.end - vRange.start) / vidDuration) * 100}%"
      ></div>
      <div class="absolute top-0 w-0.5 h-full bg-neural-400"
        style="left: {(curTime / vidDuration) * 100}%"
      ></div>
    </div>
  </div>

  <div class="flex justify-between mt-1 text-[10px] text-white/20 font-mono">
    <span>{formatTime(vRange.start)}</span>
    <span>{formatTime((vRange.start + vRange.end) / 2)}</span>
    <span>{formatTime(vRange.end)}</span>
  </div>
</div>

<style>
  svg :global(line), svg :global(circle), svg :global(rect), svg :global(polyline) {
    pointer-events: none;
  }
</style>