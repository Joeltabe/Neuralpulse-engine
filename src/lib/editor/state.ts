import { writable, derived } from 'svelte/store'
import type { Recommendation } from '$lib/types/api'

export interface EditorCut {
  time: number
  type: 'fade' | 'crossfade' | 'cut'
  enabled: boolean
}

export interface EditorSceneBreak {
  time: number
  transition: 'fade' | 'crossfade' | 'cut'
  auto_applied: boolean
}

export const videoSrc = writable('')
export const videoFile = writable<File | null>(null)
export const currentTime = writable(0)
export const duration = writable(0)
export const isPlaying = writable(false)
export const zoom = writable(1)
export const trimStart = writable(0)
export const trimEnd = writable(0)
export const recommendations = writable<Recommendation[]>([])
export const sceneBreaks = writable<EditorSceneBreak[]>([])
export const engagementCurve = writable<number[]>([])
export const timestampAxis = writable<number[]>([])
export const cuts = writable<EditorCut[]>([])
export const isExporting = writable(false)
export const exportProgress = writable(0)
export const ffmpegLoaded = writable(false)

export const visibleRange = derived([zoom, duration], ([$zoom, $duration]) => {
  const range = $duration / Math.max($zoom, 0.1)
  return { start: 0, end: Math.max(range, $duration) }
})

export const SEVERITY_STYLES = {
  critical: { bg: 'bg-red-500/15', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-400', glow: 'rgba(239,68,68,0.35)' },
  moderate: { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-400', glow: 'rgba(251,191,36,0.35)' },
  suggestion: { bg: 'bg-blue-500/15', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-400', glow: 'rgba(59,130,246,0.35)' },
} as const

export function recColor(severity: string) {
  return SEVERITY_STYLES[severity as keyof typeof SEVERITY_STYLES] || SEVERITY_STYLES.suggestion
}

export function resetEditor() {
  videoSrc.set('')
  videoFile.set(null)
  currentTime.set(0)
  duration.set(0)
  isPlaying.set(false)
  zoom.set(1)
  trimStart.set(0)
  trimEnd.set(0)
  recommendations.set([])
  sceneBreaks.set([])
  engagementCurve.set([])
  timestampAxis.set([])
  cuts.set([])
  isExporting.set(false)
  exportProgress.set(0)
}
