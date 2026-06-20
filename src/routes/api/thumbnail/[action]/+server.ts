import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import {
  apiError, validateAction, safeJsonParse, sanitizeString,
  ALLOWED_THUMBNAIL_ACTIONS, MAX_PROMPT_LEN
} from '$lib/utils/validation';

export const GET: RequestHandler = async ({ params, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_THUMBNAIL_ACTIONS);
  if (!action) return apiError(400, `Invalid thumbnail action: ${params.action}`);

  try {
    const data = await apiFetch(`/thumbnail/${action}`, {}, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Thumbnail request failed');
  }
};

export const POST: RequestHandler = async ({ params, request, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_THUMBNAIL_ACTIONS);
  if (!action) return apiError(400, `Invalid thumbnail action: ${params.action}`);

  try {
    if (action === 'generate') {
      const raw = await request.text();
      const body = safeJsonParse(raw);
      if (!body || typeof body !== 'object') return apiError(400, 'Invalid request body');

      const record = body as Record<string, unknown>;
      const prompt = sanitizeString(record.prompt as string, MAX_PROMPT_LEN);
      const modelKey = typeof record.model_key === 'string'
        ? record.model_key.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 50)
        : '';

      if (!prompt) return apiError(400, 'Prompt required');
      if (!modelKey) return apiError(400, 'Model key required');

      // Send to backend with models array format
      const data = await apiFetch('/thumbnail/generate', {
        method: 'POST',
        body: JSON.stringify({ 
          prompt, 
          models: [modelKey],
          negative_prompt: record.negative_prompt || '',
          guidance_scale: record.guidance_scale || 7.5,
          num_inference_steps: record.num_inference_steps || 35
        })
      }, token);
      return json(data);
    }

    return apiError(400, 'Unknown thumbnail action');
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Thumbnail generation failed');
  }
};
