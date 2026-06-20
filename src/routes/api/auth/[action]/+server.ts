import { json } from '@sveltejs/kit';
import { dev } from '$app/environment';
import { apiFetch } from '$lib/utils/api';
import { sanitizeEmail, validatePassword, validateAction, apiError, safeJsonParse, ALLOWED_AUTH_ACTIONS } from '$lib/utils/validation';
import type { RequestHandler } from './$types';

export const POST: RequestHandler = async ({ params, request, cookies }) => {
  const action = validateAction(params.action, ALLOWED_AUTH_ACTIONS);
  if (!action) return apiError(400, `Invalid auth action: ${params.action}`);

  try {
    if (action === 'login') {
      const body = safeJsonParse(await request.text());
      if (!body || typeof body !== 'object') return apiError(400, 'Invalid request body');
      const email = sanitizeEmail((body as Record<string, unknown>).email);
      const password = validatePassword((body as Record<string, unknown>).password);
      if (!email || !password) return apiError(400, 'Valid email and password (6+ chars) required');

      const data = await apiFetch<{ success: boolean; token?: string; user?: unknown; error?: string }>(
        '/auth/login',
        { method: 'POST', body: JSON.stringify({ email, password }) }
      );
      if (data.success && data.token) {
        cookies.set('neuralpulse_token', data.token, {
          path: '/', httpOnly: true, sameSite: 'lax', secure: !dev, maxAge: 60 * 60 * 24
        });
      }
      return json(data);
    }

    if (action === 'register') {
      const body = safeJsonParse(await request.text());
      if (!body || typeof body !== 'object') return apiError(400, 'Invalid request body');

      const record = body as Record<string, unknown>;
      const email = sanitizeEmail(record.email);
      const password = validatePassword(record.password);
      const name = typeof record.name === 'string' ? record.name.trim().slice(0, 100).replace(/<[^>]*>/g, '') : '';

      if (!email || !password) return apiError(400, 'Valid email and password (6+ chars) required');
      if (name && name.length > 100) return apiError(400, 'Name too long');

      const data = await apiFetch<{ success: boolean; token?: string; user?: unknown; error?: string }>(
        '/auth/register',
        { method: 'POST', body: JSON.stringify({ email, password, name: name || undefined }) }
      );
      if (data.success && data.token) {
        cookies.set('neuralpulse_token', data.token, {
          path: '/', httpOnly: true, sameSite: 'lax', secure: !dev, maxAge: 60 * 60 * 24
        });
      }
      return json(data);
    }

    if (action === 'demo-login') {
      const data = await apiFetch<{ success: boolean; token?: string; user?: unknown; error?: string }>(
        '/auth/demo-login', { method: 'POST' }
      );
      if (data.success && data.token) {
        cookies.set('neuralpulse_token', data.token, {
          path: '/', httpOnly: true, sameSite: 'lax', secure: !dev, maxAge: 60 * 60 * 24
        });
      }
      return json(data);
    }

    if (action === 'logout') {
      cookies.delete('neuralpulse_token', { path: '/' });
      return json({ success: true });
    }

    return apiError(400, 'Unknown action');
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : 'Authentication failed';
    return apiError(502, msg);
  }
};
