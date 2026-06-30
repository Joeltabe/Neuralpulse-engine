import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import { apiError, validateAction, ALLOWED_CHANNEL_ACTIONS } from '$lib/utils/validation';

export const POST: RequestHandler = async ({ params, request, locals }) => {
  const token = locals.token;
  const action = validateAction(params.action, ALLOWED_CHANNEL_ACTIONS);
  if (!action) return apiError(400, `Invalid channel action: ${params.action}`);

  try {
    const body = await request.json();
    const headers: Record<string, string> = { 'Content-Type': 'application/json' };
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const data = await apiFetch(`/channel/${action}`, {
      method: 'POST',
      body: JSON.stringify(body),
      headers,
    }, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Channel request failed');
  }
};

export const GET: RequestHandler = async ({ params, locals }) => {
  const token = locals.token;
  const action = validateAction(params.action, ALLOWED_CHANNEL_ACTIONS);
  if (!action) return apiError(400, `Invalid channel action: ${params.action}`);

  if (action !== 'profile') return apiError(400, `GET only supported for profile action`);

  try {
    const data = await apiFetch('/channel/profile', {}, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Channel request failed');
  }
};
