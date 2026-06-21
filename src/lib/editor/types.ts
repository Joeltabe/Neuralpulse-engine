export interface EditorRecommendation {
  timestamp_sec: number
  severity: 'critical' | 'moderate' | 'suggestion'
  category: string
  title: string
  description: string
  suggestion: string
  expected_impact: number
}

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

export interface EditorState {
  videoSrc: string
  videoFile: File | null
  currentTime: number
  duration: number
  isPlaying: boolean
  zoom: number
  trimStart: number
  trimEnd: number
  recommendations: EditorRecommendation[]
  sceneBreaks: EditorSceneBreak[]
  engagementCurve: number[]
  timestampAxis: number[]
  cuts: EditorCut[]
  isExporting: boolean
  exportProgress: number
  loadFFmpeg: boolean
}

export function createEditorState(): EditorState {
  return {
    videoSrc: '',
    videoFile: null,
    currentTime: 0,
    duration: 0,
    isPlaying: false,
    zoom: 1,
    trimStart: 0,
    trimEnd: 0,
    recommendations: [],
    sceneBreaks: [],
    engagementCurve: [],
    timestampAxis: [],
    cuts: [],
    isExporting: false,
    exportProgress: 0,
    loadFFmpeg: false,
  }
}

export const SEVERITY_COLORS = {
  critical: { bg: 'bg-red-500/15', border: 'border-red-500/30', text: 'text-red-400', dot: 'bg-red-400' },
  moderate: { bg: 'bg-amber-500/15', border: 'border-amber-500/30', text: 'text-amber-400', dot: 'bg-amber-400' },
  suggestion: { bg: 'bg-blue-500/15', border: 'border-blue-500/30', text: 'text-blue-400', dot: 'bg-blue-400' },
} as const

export const CATEGORY_ICONS: Record<string, string> = {
  hook: '🎯',
  reward: '💎',
  memory: '🧠',
  attention: '👁️',
  pacing: '⏱️',
  audio: '🔊',
  copy: '✍️',
  emotional: '💫',
  visual: '🎬',
}
