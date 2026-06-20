import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import { apiError, validateAction, ALLOWED_HISTORY_ACTIONS } from '$lib/utils/validation';

export const GET: RequestHandler = async ({ params, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_HISTORY_ACTIONS);
  if (!action) return apiError(400, `Invalid history action: ${params.action}`);

  try {
    const data = await apiFetch(`/history/${action}`, {}, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'History request failed');
  }
};
