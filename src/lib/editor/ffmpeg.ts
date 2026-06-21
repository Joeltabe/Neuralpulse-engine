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

export async function exportVideo(
  file: File,
  trimStart: number,
  trimEnd: number,
  cuts: { time: number; type: string; enabled: boolean }[],
  onProgress: (progress: number) => void,
): Promise<Blob> {
  const ff = await loadFFmpeg()

  ff.on('progress', ({ progress: p }) => {
    onProgress(Math.round(p * 100))
  })

  const inputName = 'input.mp4'
  const outputName = 'output.mp4'

  await ff.writeFile(inputName, await fetchFile(file))

  const duration = trimEnd - trimStart
  const enabledCuts = cuts.filter(c => c.enabled && c.time > trimStart && c.time < trimEnd).map(c => c.time).sort((a, b) => a - b)

  if (enabledCuts.length === 0) {
    await ff.exec([
      '-i', inputName,
      '-ss', String(trimStart),
      '-to', String(trimEnd),
      '-c:v', 'libx264',
      '-preset', 'fast',
      '-crf', '22',
      '-c:a', 'aac',
      '-movflags', '+faststart',
      outputName,
    ])
  } else {
    const filterParts: string[] = []
    let lastEnd = trimStart
    for (const cut of enabledCuts) {
      filterParts.push(`between(t,${lastEnd},${cut})`)
      lastEnd = cut
    }
    filterParts.push(`between(t,${lastEnd},${trimEnd})`)

    const selectExpr = filterParts.map(p => `(${p})`).join('+')
    await ff.exec([
      '-i', inputName,
      '-ss', String(trimStart),
      '-to', String(trimEnd),
      '-vf', `select='${selectExpr}',setpts=N/FRAME_RATE/TB`,
      '-af', `aselect='${selectExpr}',asetpts=N/SR/TB`,
      '-c:v', 'libx264',
      '-preset', 'fast',
      '-crf', '22',
      '-c:a', 'aac',
      '-movflags', '+faststart',
      outputName,
    ])
  }

  const data = await ff.readFile(outputName)
  await ff.deleteFile(inputName)
  await ff.deleteFile(outputName)

  return new Blob([data], { type: 'video/mp4' })
}
