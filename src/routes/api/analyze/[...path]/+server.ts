import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import { apiError } from '$lib/utils/validation';
import { env } from '$env/dynamic/private';

const API_BASE = env.API_URL || 'http://localhost:8000';

export const GET: RequestHandler = async ({ params, url }) => {
  const path = params.path || '';
  const backendUrl = `${API_BASE}/analyze/${path}${url.search}`;

  try {
    const resp = await fetch(backendUrl, {
      method: 'GET',
      headers: { 'Accept': '*/*' },
      signal: AbortSignal.timeout(30000),
    });
    if (!resp.ok) {
      return new Response(await resp.text(), { status: resp.status, statusText: resp.statusText });
    }
    const blob = await resp.blob();
    return new Response(blob, {
      status: resp.status,
      headers: {
        'Content-Type': resp.headers.get('Content-Type') || 'application/octet-stream',
        'Content-Length': resp.headers.get('Content-Length') || String(blob.size),
        'Accept-Ranges': 'bytes',
      },
    });
  } catch (e: unknown) {
    return apiError(502, e instanceof Error ? e.message : 'Request failed');
  }
};