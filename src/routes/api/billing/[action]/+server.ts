import { json } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import type { RequestHandler } from './$types';
import { validateAction, apiError, safeJsonParse, ALLOWED_BILLING_ACTIONS } from '$lib/utils/validation';

export const GET: RequestHandler = async ({ params, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_BILLING_ACTIONS);
  if (!action) return apiError(400, `Invalid billing action: ${params.action}`);

  try {
    const data = await apiFetch(`/billing/${action}`, {}, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Billing request failed');
  }
};

export const POST: RequestHandler = async ({ params, request, locals }) => {
  const token = locals.token;
  if (!token) return apiError(401, 'Not authenticated');

  const action = validateAction(params.action, ALLOWED_BILLING_ACTIONS);
  if (!action) return apiError(400, `Invalid billing action: ${params.action}`);

  try {
    const raw = await request.text();
    const body = safeJsonParse(raw);
    if (!body || typeof body !== 'object') return apiError(400, 'Invalid request body');

    const data = await apiFetch(`/billing/${action}`, {
      method: 'POST', body: JSON.stringify(body)
    }, token);
    return json(data);
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Billing request failed');
  }
};
