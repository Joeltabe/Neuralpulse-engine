import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import {
  validateAction, sanitizeString, safeJsonParse,
  apiError, MAX_TEXT_LEN, MAX_BODY_SIZE
} from '$lib/utils/validation';

const ALLOWED_AUTHENTICITY_ACTIONS = ['analyze', 'index', 'provenance-register', 'provenance-lookup', 'history'] as const;

export const GET: RequestHandler = async ({ params, url, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_AUTHENTICITY_ACTIONS);
  if (!action) return apiError(400, `Invalid authenticity action: ${params.action}`);

  try {
    if (action === 'provenance-lookup') {
      const contentHash = url.searchParams.get('content_hash');
      if (!contentHash) return apiError(400, 'content_hash query parameter required');
      const data = await apiFetch(
        `/authenticity/provenance/lookup?content_hash=${encodeURIComponent(contentHash)}`,
        {},
        token
      );
      return json(data);
    }

    if (action === 'history') {
      const data = await apiFetch('/authenticity/history', {}, token);
      return json(data);
    }

    return apiError(400, `GET not supported for action: ${action}`);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Authenticity request failed');
  }
};

export const POST: RequestHandler = async ({ params, request, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_AUTHENTICITY_ACTIONS);
  if (!action) return apiError(400, `Invalid authenticity action: ${params.action}`);

  try {
    if (action === 'analyze') {
      const ct = request.headers.get('content-type') || '';
      if (ct.includes('multipart/form-data')) {
        const form = await request.formData();
        const file = form.get('file');
        if (!file || !(file instanceof File)) return apiError(400, 'File required for file analysis');
        const data = await apiFetch('/authenticity/analyze', { method: 'POST', body: form }, token);
        return json(data);
      }

      const raw = await request.text();
      if (raw.length > MAX_BODY_SIZE) return apiError(413, 'Request body too large');
      const body = safeJsonParse(raw);
      if (!body || typeof body !== 'object') return apiError(400, 'Invalid JSON body');
      const record = body as Record<string, unknown>;
      const textStr = sanitizeString(record.text, MAX_TEXT_LEN);
      if (!textStr) return apiError(400, 'Text content required or too long');
      const data = await apiFetch('/authenticity/analyze', {
        method: 'POST', body: JSON.stringify({ text: textStr })
      }, token);
      return json(data);
    }

    if (action === 'index') {
      const raw = await request.text();
      if (raw.length > MAX_BODY_SIZE) return apiError(413, 'Request body too large');
      const body = safeJsonParse(raw);
      if (!body || typeof body !== 'object') return apiError(400, 'Invalid JSON body');
      const record = body as Record<string, unknown>;
      const textStr = sanitizeString(record.text, MAX_TEXT_LEN);
      if (!textStr) return apiError(400, 'Text content required or too long');
      const data = await apiFetch('/authenticity/index', {
        method: 'POST', body: JSON.stringify({ text: textStr })
      }, token);
      return json(data);
    }

    if (action === 'provenance-register') {
      const form = await request.formData();
      const file = form.get('file');
      if (!file || !(file instanceof File)) return apiError(400, 'File required for provenance registration');
      const data = await apiFetch('/authenticity/provenance/register', { method: 'POST', body: form }, token);
      return json(data);
    }

    return apiError(400, `POST not supported for action: ${action}`);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Authenticity request failed');
  }
};
