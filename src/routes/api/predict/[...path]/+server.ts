import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import { apiError, validateFileType, validateFileSize, MAX_FILE_SIZE, ALLOWED_VIDEO_TYPES } from '$lib/utils/validation';

export const POST: RequestHandler = async ({ request, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  try {
    const form = await request.formData();
    const file = form.get('file') as File | null;
    if (!file || !(file instanceof File)) return apiError(400, 'File required');
    if (!validateFileSize(file, MAX_FILE_SIZE)) return apiError(413, 'File too large (max 500MB)');

    const data = await apiFetch('/api/predict-brain', { method: 'POST', body: form }, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Prediction failed');
  }
};
