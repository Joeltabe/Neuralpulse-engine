import { FFmpeg } from '@ffmpeg/ffmpeg'
import { fetchFile, toBlobURL } from '@ffmpeg/util'

let ffmpeg: FFmpeg | null = null
let loaded = false

export async function loadFFmpeg(): Promise<FFmpeg> {
  if (loaded && ffmpeg) return ffmpeg

  ffmpeg = new FFmpeg()

  const baseURL = 'https://unpkg.com/@ffmpeg/core@0.12.6/dist/esm'

  await ffmpeg.load({
    coreURL: await toBlobURL(`${baseURL}/ffmpeg-core.js`, 'text/javascript'),
    wasmURL: await toBlobURL(`${baseURL}/ffmpeg-core.wasm`, 'application/wasm'),
  })

  loaded = true
  return ffmpeg
}

export interface ExportOptions {
  format: 'mp4' | 'webm' | 'gif'
  resolution: 'source' | '1080p' | '720p' | '480p'
  quality: 'high' | 'medium' | 'low'
  preset: string
}

export const RESOLUTION_MAP: Record<string, string | null> = {
  source: null,
  '1080p': '1920:1080',
  '720p': '1280:720',
  '480p': '854:480',
}

export const QUALITY_MAP: Record<string, { crf: number; audio_bitrate: string }> = {
  high: { crf: 18, audio_bitrate: '192k' },
  medium: { crf: 23, audio_bitrate: '128k' },
  low: { crf: 28, audio_bitrate: '64k' },
}

export async function exportVideo(
  file: File,
  trimStart: number,
  trimEnd: number,
  cuts: { time: number; type: string; enabled: boolean }[],
  options: ExportOptions,
  onProgress: (progress: number) => void,
): Promise<Blob> {
  const ff = await loadFFmpeg()
  const QUALITY = QUALITY_MAP[options.quality] || QUALITY_MAP.medium
  const SCALE = RESOLUTION_MAP[options.resolution]

  ff.on('progress', ({ progress: p }) => {
    onProgress(Math.round(p * 100))
  })

  const inputName = `input${file.name.match(/\.\w+$/)?.[0] || '.mp4'}`
  const ext = options.format === 'webm' ? 'webm' : options.format === 'gif' ? 'gif' : 'mp4'
  const outputName = `output.${ext}`

  await ff.writeFile(inputName, await fetchFile(file))

  const enabledCuts = cuts.filter(c => c.enabled && c.time > trimStart && c.time < trimEnd).map(c => c.time).sort((a, b) => a - b)

  const baseArgs: string[] = ['-i', inputName, '-ss', String(trimStart), '-to', String(trimEnd)]

  if (options.format === 'gif') {
    const paletteName = 'palette.png'
    const filterGraph = `fps=10,scale=${SCALE || 'iw'}:${SCALE ? 'ih' : 'iw'}:flags=lanczos`
    await ff.exec([...baseArgs, '-vf', `${filterGraph},palettegen=stats_mode=diff`, '-y', paletteName])
    await ff.exec([...baseArgs, '-i', paletteName, '-lavfi', `${filterGraph}[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=5`, '-y', outputName])
    const data = await ff.readFile(outputName)
    await ff.deleteFile(inputName)
    await ff.deleteFile(outputName)
    await ff.deleteFile(paletteName)
    return new Blob([data], { type: 'image/gif' })
  }

  if (options.format === 'webm') {
    if (enabledCuts.length === 0) {
      await ff.exec([
        ...baseArgs,
        ...(SCALE ? ['-vf', `scale=${SCALE}`] : []),
        '-c:v', 'libvpx-vp9',
        '-crf', String(QUALITY.crf + 5),
        '-b:v', '0',
        '-c:a', 'libopus',
        '-b:a', QUALITY.audio_bitrate,
        '-row-mt', '1',
        outputName,
      ])
    } else {
      const selectExpr = buildSelectExpr(trimStart, trimEnd, enabledCuts)
      await ff.exec([
        ...baseArgs,
        '-vf', `${SCALE ? `scale=${SCALE},` : ''}select='${selectExpr}',setpts=N/FRAME_RATE/TB`,
        '-af', `aselect='${selectExpr}',asetpts=N/SR/TB`,
        '-c:v', 'libvpx-vp9',
        '-crf', String(QUALITY.crf + 5),
        '-b:v', '0',
        '-c:a', 'libopus',
        '-b:a', QUALITY.audio_bitrate,
        '-row-mt', '1',
        outputName,
      ])
    }
  } else {
    if (enabledCuts.length === 0) {
      await ff.exec([
        ...baseArgs,
        ...(SCALE ? ['-vf', `scale=${SCALE}`] : []),
        '-c:v', 'libx264',
        '-preset', options.preset || 'fast',
        '-crf', String(QUALITY.crf),
        '-c:a', 'aac',
        '-b:a', QUALITY.audio_bitrate,
        '-movflags', '+faststart',
        outputName,
      ])
    } else {
      const selectExpr = buildSelectExpr(trimStart, trimEnd, enabledCuts)
      await ff.exec([
        ...baseArgs,
        '-vf', `${SCALE ? `scale=${SCALE},` : ''}select='${selectExpr}',setpts=N/FRAME_RATE/TB`,
        '-af', `aselect='${selectExpr}',asetpts=N/SR/TB`,
        '-c:v', 'libx264',
        '-preset', options.preset || 'fast',
        '-crf', String(QUALITY.crf),
        '-c:a', 'aac',
        '-b:a', QUALITY.audio_bitrate,
        '-movflags', '+faststart',
        outputName,
      ])
    }
  }

  const data = await ff.readFile(outputName)
  await ff.deleteFile(inputName)
  await ff.deleteFile(outputName)

  const mimeTypes: Record<string, string> = {
    mp4: 'video/mp4',
    webm: 'video/webm',
    gif: 'image/gif',
  }
  return new Blob([data], { type: mimeTypes[ext] || 'video/mp4' })
}

function buildSelectExpr(trimStart: number, trimEnd: number, cuts: number[]): string {
  const filterParts: string[] = []
  let lastEnd = trimStart
  for (const cut of cuts) {
    filterParts.push(`between(t,${lastEnd},${cut})`)
    lastEnd = cut
  }
  filterParts.push(`between(t,${lastEnd},${trimEnd})`)
  return filterParts.map(p => `(${p})`).join('+')
}