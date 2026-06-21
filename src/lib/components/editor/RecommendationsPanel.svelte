<script lang="ts">
  import { currentTime, duration, recommendations, recColor } from '$lib/editor/state'

  let recs: any[] = []
  let subs: (() => void)[] = []
  subs.push(recommendations.subscribe(v => recs = v))
  import { onDestroy } from 'svelte'
  onDestroy(() => subs.forEach(u => u()))

  function seekTo(time: number) {
    currentTime.set(time)
  }

  function formatTime(s: number): string {
    if (!isFinite(s) || s < 0) return '0:00'
    const m = Math.floor(s / 60)
    const sec = Math.floor(s % 60)
    return `${m}:${sec.toString().padStart(2, '0')}`
  }

  let curTime = 0
  currentTime.subscribe(v => curTime = v)

  const SEVERITY_ORDER: Record<string, number> = { critical: 0, moderate: 1, suggestion: 2 }

  let sortedRecs = $derived([...recs].sort((a, b) => {
    const sa = SEVERITY_ORDER[a.severity] ?? 99
    const sb = SEVERITY_ORDER[b.severity] ?? 99
    if (sa !== sb) return sa - sb
    return b.expected_impact - a.expected_impact
  }))
</script>

<div class="flex flex-col h-full">
  <div class="px-4 py-3 border-b border-white/5">
    <h3 class="text-sm font-semibold flex items-center gap-2">
      Recommendations
      <span class="text-[10px] text-white/30 font-normal">({recs.length})</span>
    </h3>
  </div>

  <div class="flex-1 overflow-y-auto px-3 py-2 space-y-1.5">
    {#each sortedRecs as rec, i}
      <button
        onclick={() => seekTo(rec.timestamp_sec)}
        class="w-full text-left p-3 rounded-xl transition-all duration-200 cursor-pointer {Math.abs(rec.timestamp_sec - curTime) < 1 ? 'ring-1 ring-white/10 bg-white/5' : 'bg-white/[0.02]'}"
        style="border-left: 3px solid {recColor(rec.severity).glow.replace('0.35', '0.7')}"
      >
        <div class="flex items-start gap-2">
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class={`px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider ${recColor(rec.severity).bg} ${recColor(rec.severity).text}`}>
                {rec.severity}
              </span>
              <span class="text-[10px] text-white/30 font-mono">
                {rec.timestamp_sec > 0 ? `at ${formatTime(rec.timestamp_sec)}` : ''}
              </span>
            </div>
            <p class="text-sm font-medium text-white/90 leading-tight">{rec.title}</p>
            <p class="text-xs text-white/50 mt-0.5 leading-relaxed line-clamp-2">{rec.suggestion}</p>
            <div class="flex items-center gap-2 mt-1.5">
              <div class="flex-1 h-1 rounded-full bg-white/5 overflow-hidden">
                <div
                  class="h-full rounded-full"
                  class:bg-red-400={rec.severity === 'critical'}
                  class:bg-amber-400={rec.severity === 'moderate'}
                  class:bg-blue-400={rec.severity === 'suggestion'}
                  style="width: {rec.expected_impact * 100}%"
                ></div>
              </div>
              <span class={`text-[10px] font-mono ${recColor(rec.severity).text}`}>
                {Math.round(rec.expected_impact * 100)}%
              </span>
            </div>
          </div>
        </div>
      </button>
    {/each}
  </div>
</div>
