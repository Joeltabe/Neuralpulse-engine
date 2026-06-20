import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import { apiError, safeJsonParse, sanitizeString, MAX_TEXT_LEN } from '$lib/utils/validation';

export const POST: RequestHandler = async ({ request, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  try {
    const raw = await request.text();
    const body = safeJsonParse(raw);
    if (!body || typeof body !== 'object') return apiError(400, 'Invalid request body');

    const record = body as Record<string, unknown>;
    if (record.content) record.content = sanitizeString(record.content as string, MAX_TEXT_LEN) || '';
    if (record.original) record.original = sanitizeString(record.original as string, MAX_TEXT_LEN) || '';
    if (record.text) record.text = sanitizeString(record.text as string, MAX_TEXT_LEN) || '';

    const data = await apiFetch('/copy/analyze', {
      method: 'POST', body: JSON.stringify(record)
    }, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Copy analysis failed');
  }
};
