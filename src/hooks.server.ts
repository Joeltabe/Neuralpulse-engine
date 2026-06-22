import type { Handle } from '@sveltejs/kit';
import { apiFetch } from '$lib/utils/api';
import { dev } from '$app/environment';

const CSP = dev
  ? "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self' ws://localhost:* http://localhost:*; img-src 'self' data: blob:; media-src 'self' data: blob:; frame-ancestors 'none'; form-action 'self'"
  : "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: blob:; media-src 'self' data: blob:; frame-ancestors 'none'; form-action 'self'";

export const handle: Handle = async ({ event, resolve }) => {
  const token = event.cookies.get('neuralpulse_token');
  event.locals.token = token || null;
  event.locals.user = null;

  if (token) {
    try {
      const data = await apiFetch<{ success: boolean; user: App.Locals['user'] }>(
        '/auth/me', {}, token
      );
      if (data.success && data.user) {
        event.locals.user = data.user;
      }
    } catch {
      event.cookies.delete('neuralpulse_token', { path: '/' });
      event.locals.token = null;
    }
  }

  const response = await resolve(event);

  if (response.headers.get('content-type')?.startsWith('text/html')) {
    response.headers.set('X-Content-Type-Options', 'nosniff');
    response.headers.set('X-Frame-Options', 'DENY');
    response.headers.set('X-XSS-Protection', '1; mode=block');
    response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
    response.headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
    response.headers.set('Content-Security-Policy', CSP);
  }

  return response;
};
