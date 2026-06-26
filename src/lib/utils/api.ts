import { env } from '$env/dynamic/private';

const API_BASE = env.API_URL || 'http://localhost:8000';
const TIMEOUT_MS = 120_000;

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string | null,
  rawResponse?: false,
): Promise<T>;
export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  token?: string | null,
  rawResponse?: boolean,
): Promise<T | Response> {
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), TIMEOUT_MS);

  try {
    const res = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
      signal: controller.signal,
    });

    if (!res.ok) {
      const body = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(body.error || `Request failed: ${res.status}`);
    }

    if (rawResponse) return res;
    return res.json();
  } finally {
    clearTimeout(timeoutId);
  }
}
