import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import {
  ALLOWED_ANALYSIS_TYPES, ALLOWED_VIDEO_TYPES, ALLOWED_AUDIO_TYPES, ALLOWED_TEXT_TYPES,
  validateAction, validateFileType, validateFileSize,
  sanitizeString, apiError, MAX_FILE_SIZE, MAX_TEXT_LEN, MAX_BODY_SIZE
} from '$lib/utils/validation';

export const POST: RequestHandler = async ({ params, request, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const type = validateAction(params.type, ALLOWED_ANALYSIS_TYPES);
  if (!type) return apiError(400, `Invalid analysis type: ${params.type}`);

  try {
    if (type === 'text') {
      const raw = await request.text();
      if (raw.length > MAX_BODY_SIZE) return apiError(413, 'Request body too large');

      const body = parseJsonSafe(raw);
      if (!body || typeof body !== 'object') return apiError(400, 'Invalid JSON body');

      const record = body as Record<string, unknown>;
      const text = sanitizeString(record.text, MAX_TEXT_LEN);
      if (!text) return apiError(400, 'Text content required or too long');

      const data = await apiFetch('/analyze/text', {
        method: 'POST', body: JSON.stringify({ text, filename: record.filename || 'text_input' })
      }, token);
      return json(data);
    }

    if (type === 'ab-test') {
      const form = await request.formData();
      const mode = form.get('mode') as string | null;
      if (!mode || !['video', 'audio', 'text'].includes(mode)) return apiError(400, 'A/B test mode required (video/audio/text)');

      if (mode === 'text') {
        const rawTexts = form.get('texts') as string | null;
        const variantNames = form.get('variant_names') as string | null;
        if (!rawTexts) return apiError(400, 'Texts required for A/B test');

        const texts = parseJsonSafe(rawTexts);
        if (!Array.isArray(texts) || texts.length < 2) return apiError(400, 'At least 2 text variants required');

        const names = variantNames ? parseJsonSafe(variantNames) : null;
        const data = await apiFetch('/analyze/ab-test/text', {
          method: 'POST', body: JSON.stringify({ texts, variant_names: names })
        }, token);
        return json(data);
      }

      const files = form.getAll('files') as File[];
      if (files.length < 2) return apiError(400, 'At least 2 files required for A/B test');

      const endpoint = mode === 'video' ? '/analyze/ab-test/video' : '/analyze/ab-test/audio';
      const variantNames = form.get('variant_names') as string | null;
      const body = new FormData();
      files.forEach(f => body.append('files', f));
      if (variantNames) body.append('variant_names', variantNames);

      const data = await apiFetch(endpoint, { method: 'POST', body }, token);
      return json(data);
    }

    if (type === 'video' || type === 'audio' || type === 'upload-text') {
      const form = await request.formData();
      const file = form.get('file') as File | null;
      if (!file || !(file instanceof File)) return apiError(400, 'File required');

      if (!validateFileSize(file, MAX_FILE_SIZE)) return apiError(413, 'File too large (max 500MB)');

      if (type === 'video') {
        if (!validateFileType(file, ALLOWED_VIDEO_TYPES)) return apiError(415, 'Unsupported video format (mp4, webm, mov, avi)');
      }
      if (type === 'audio') {
        if (!validateFileType(file, ALLOWED_AUDIO_TYPES)) return apiError(415, 'Unsupported audio format (mp3, wav, ogg, mp4, webm)');
      }
      if (type === 'upload-text') {
        if (!validateFileType(file, ALLOWED_TEXT_TYPES)) return apiError(415, 'Unsupported text format (txt, csv, json)');
      }

      const data = await apiFetch(`/analyze/${type}`, { method: 'POST', body: form }, token);
      return json(data);
    }

    return apiError(400, 'Unknown analysis type');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Analysis failed';
    return apiError(502, msg);
  }
};

function parseJsonSafe(text: string): unknown {
  try { return JSON.parse(text); } catch { return null; }
}
