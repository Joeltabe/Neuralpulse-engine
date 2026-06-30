import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import { apiError } from '$lib/utils/validation';

const ALLOWED_ACTIONS = [
  'search', 'channel', 'video', 'popular', 'categories',
  'analytics', 'analyze', 'auth-url', 'oauth-callback', 'upload',
  'playlists', 'ingest-channel',
] as const;

export const GET: RequestHandler = async ({ params, url, locals }) => {
  const action = params.action;
  if (!ALLOWED_ACTIONS.includes(action as typeof ALLOWED_ACTIONS[number])) {
    return apiError(400, `Invalid action: ${action}`);
  }
  try {
    const queryStr = url.searchParams.toString();
    const endpoint = `/youtube/${action}${queryStr ? '?' + queryStr : ''}`;
    const data = await apiFetch(endpoint, {}, locals.token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'YouTube request failed');
  }
};

export const POST: RequestHandler = async ({ params, request, locals }) => {
  const action = params.action;
  if (!ALLOWED_ACTIONS.includes(action as typeof ALLOWED_ACTIONS[number])) {
    return apiError(400, `Invalid action: ${action}`);
  }
  try {
    const body = await request.json();
    const data = await apiFetch(`/youtube/${action}`, {
      method: 'POST',
      body: JSON.stringify(body),
    }, locals.token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'YouTube request failed');
  }
};
