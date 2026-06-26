<script lang="ts">
  import { onDestroy } from 'svelte'
  import { currentTime, duration, transcriptSegments, wordLevelScores } from '$lib/editor/state'
  import type { WordScore } from '$lib/types/api'

  interface TranscriptSegment {
    start: number; end: number; text: string; attention_score: number
    _editing?: boolean; _draft?: string
  }

  let segments: TranscriptSegment[] = []
  let words: WordScore[] = []
  let curTime = 0
  let vidDuration = 0
  let subs: (() => void)[] = []

  subs.push(transcriptSegments.subscribe(v => {
    segments = v.map(s => ({ ...s, _editing: false, _draft: s.text }))
  }))
  subs.push(wordLevelScores.subscribe(v => words = v))
  subs.push(currentTime.subscribe(v => curTime = v))
  subs.push(duration.subscribe(v => vidDuration = v))

  onDestroy(() => subs.forEach(u => u()))

  function seekTo(time: number) { currentTime.set(time) }

  function formatTime(s: number): string {
    if (!isFinite(s) || s < 0) return '0:00'
    const m = Math.floor(s / 60); const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  function startEdit(seg: TranscriptSegment) { seg._editing = true; seg._draft = seg.text }

  function saveEdit(seg: TranscriptSegment) {
    seg.text = seg._draft || seg.text; seg._editing = false
    transcriptSegments.update(prev =>
      prev.map(s => s.start === seg.start && s.end === seg.end ? { ...seg, text: seg.text } : s)
    )
  }

  function cancelEdit(seg: TranscriptSegment) { seg._editing = false; seg._draft = seg.text }

  function handleKeydown(e: KeyboardEvent, seg: TranscriptSegment) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); saveEdit(seg) }
    if (e.key === 'Escape') cancelEdit(seg)
  }

  function exportSRT() {
    const sorted = [...segments].sort((a, b) => a.start - b.start)
    let srt = ''
    sorted.forEach((seg, i) => {
      srt += `${i + 1}\n${formatSrtTime(seg.start)} --> ${formatSrtTime(seg.end)}\n${seg.text}\n\n`
    })
    const blob = new Blob([srt], { type: 'text/plain' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = 'transcript.srt'; a.click(); URL.revokeObjectURL(url)
  }

  function exportTXT() {
    const sorted = [...segments].sort((a, b) => a.start - b.start)
    const txt = sorted.map(s => `[${formatTime(s.start)} - ${formatTime(s.end)}] ${s.text}`).join('\n')
    const blob = new Blob([txt], { type: 'text/plain' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = 'transcript.txt'; a.click(); URL.revokeObjectURL(url)
  }

  function formatSrtTime(s: number): string {
    const h = Math.floor(s / 3600); const m = Math.floor((s % 3600) / 60)
    const sec = Math.floor(s % 60); const ms = Math.floor((sec % 1) * 1000)
    return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(Math.floor(sec)).padStart(2, '0')},${String(ms).padStart(3, '0')}`
  }

  function wordColor(score: number): string {
    if (score >= 0.7) return 'text-emerald-400'
    if (score >= 0.5) return 'text-white/90'
    if (score >= 0.3) return 'text-white/50'
    return 'text-white/20'
  }

  function splitSegment(seg: TranscriptSegment) {
    transcriptSegments.update(prev => {
      const idx = prev.findIndex(s => s.start === seg.start && s.end === seg.end)
      if (idx === -1) return prev
      const mid = (seg.start + seg.end) / 2
      const half = Math.ceil(seg.text.length / 2)
      const newSeg1 = { ...seg, end: mid, text: seg.text.slice(0, half) }
      const newSeg2 = { ...seg, start: mid, text: seg.text.slice(half) }
      return [...prev.slice(0, idx), newSeg1, newSeg2, ...prev.slice(idx + 1)]
    })
  }

  function mergeWithNext(seg: TranscriptSegment) {
    transcriptSegments.update(prev => {
      const idx = prev.findIndex(s => s.start === seg.start && s.end === seg.end)
      if (idx === -1 || idx >= prev.length - 1) return prev
      const next = prev[idx + 1]
      const merged = { ...seg, end: next.end, text: seg.text + ' ' + next.text }
      return [...prev.slice(0, idx), merged, ...prev.slice(idx + 2)]
    })
  }

  function removeSegment(seg: TranscriptSegment) {
    transcriptSegments.update(prev => prev.filter(s => !(s.start === seg.start && s.end === seg.end)))
  }
</script>

<div class="flex flex-col h-full">
  <div class="flex items-center justify-between px-4 py-3 border-b border-white/5">
    <h3 class="text-sm font-semibold flex items-center gap-2">
      Transcript
      <span class="text-[10px] text-white/30 font-normal">({segments.length} segments)</span>
    </h3>
    <div class="flex gap-1">
      <button onclick={exportSRT}
        class="px-2 py-1 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80 transition-colors"
        title="Export SRT">SRT</button>
      <button onclick={exportTXT}
        class="px-2 py-1 rounded-lg text-[10px] font-medium bg-white/5 hover:bg-white/10 text-white/50 hover:text-white/80 transition-colors"
        title="Export TXT">TXT</button>
    </div>
  </div>

  <div class="flex-1 overflow-y-auto px-3 py-2 space-y-1">
    {#each segments as seg, i}
      <div
        class="group rounded-xl transition-all duration-150 {curTime >= seg.start && curTime <= seg.end ? 'ring-1 ring-neural-500/30 bg-neural-500/5' : 'bg-white/[0.02] hover:bg-white/5'}"
      >
        <button onclick={() => seekTo(seg.start)}
          class="w-full text-left px-3 pt-2 pb-1 text-[10px] font-mono text-white/30 hover:text-white/50 transition-colors"
        >{formatTime(seg.start)} — {formatTime(seg.end)}</button>

        {#if seg._editing}
          <div class="px-3 pb-2">
            <textarea bind:value={seg._draft}
              onkeydown={(e) => handleKeydown(e, seg)}
              class="w-full bg-white/5 border border-white/10 rounded-lg px-3 py-2 text-sm text-white/90 resize-none focus:outline-none focus:border-neural-500/50 transition-colors"
              style="min-height: 60px"
            ></textarea>
            <div class="flex gap-2 mt-1">
              <button onclick={() => saveEdit(seg)}
                class="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-neural-500/20 text-neural-400 hover:bg-neural-500/30 transition-colors">Save</button>
              <button onclick={() => cancelEdit(seg)}
                class="px-2.5 py-1 rounded-lg text-[10px] font-medium bg-white/5 text-white/50 hover:bg-white/10 transition-colors">Cancel</button>
            </div>
          </div>
        {:else}
          <div onclick={() => startEdit(seg)} class="px-3 pb-2 cursor-text">
            {#if words.length > 0}
              <p class="text-sm leading-relaxed">
                {#each seg.text.split(' ') as word, wi}
                  {@const wordScore = words.find(w =>
                    Math.abs(w.timestamp - (seg.start + (wi / seg.text.split(' ').length) * (seg.end - seg.start))) < 0.3
                  )}
                  <span class={wordScore ? wordColor(wordScore.attention) : 'text-white/80'}>{word} </span>
                {/each}
              </p>
            {:else}
              <p class="text-sm text-white/80 leading-relaxed">{seg.text}</p>
            {/if}
            <div class="flex items-center gap-2 mt-1">
              <div class="flex-1 h-0.5 rounded-full bg-white/5 overflow-hidden">
                <div class="h-full rounded-full bg-neural-500/50 transition-all" style="width: {seg.attention_score * 100}%"></div>
              </div>
              <span class="text-[10px] font-mono text-white/30">{Math.round(seg.attention_score * 100)}%</span>
            </div>
          </div>
          <div class="px-3 pb-1.5 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button onclick={() => splitSegment(seg)}
              class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-white/5 hover:bg-white/10 text-white/30 hover:text-white/60 transition-colors">Split</button>
            <button onclick={() => mergeWithNext(seg)}
              class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-white/5 hover:bg-white/10 text-white/30 hover:text-white/60 transition-colors">Merge</button>
            <button onclick={() => removeSegment(seg)}
              class="px-1.5 py-0.5 rounded text-[9px] font-medium bg-red-500/10 hover:bg-red-500/20 text-red-400/50 hover:text-red-400 transition-colors">Remove</button>
          </div>
        {/if}
      </div>
    {:else}
      <div class="text-center py-12">
        <p class="text-sm text-white/30">No transcript available</p>
        <p class="text-xs text-white/20 mt-1">Transcript data is generated during video/audio analysis</p>
      </div>
    {/each}
  </div>
</div>
