import { json } from '@sveltejs/kit';

export const MAX_EMAIL_LEN = 254;
export const MAX_NAME_LEN = 100;
export const MAX_PASSWORD_LEN = 128;
export const MIN_PASSWORD_LEN = 6;
export const MAX_TEXT_LEN = 50000;
export const MAX_PROMPT_LEN = 2000;
export const MAX_FILE_SIZE = 500 * 1024 * 1024;
export const MAX_BODY_SIZE = 1024 * 1024;

export const ALLOWED_ANALYSIS_TYPES = ['video', 'audio', 'text', 'upload-text', 'ab-test'] as const;
export const ALLOWED_AUTH_ACTIONS = ['login', 'register', 'demo-login', 'logout'] as const;
export const ALLOWED_HISTORY_ACTIONS = ['analyses', 'stats'] as const;
export const ALLOWED_BILLING_ACTIONS = ['packages', 'balance', 'purchase', 'history'] as const;
export const ALLOWED_THUMBNAIL_ACTIONS = ['generate', 'models', 'history'] as const;

export const ALLOWED_VIDEO_TYPES = ['video/mp4', 'video/webm', 'video/quicktime', 'video/x-msvideo'];
export const ALLOWED_AUDIO_TYPES = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4', 'audio/webm'];
export const ALLOWED_TEXT_TYPES = ['text/plain', 'text/csv', 'application/json'];

const HTML_TAG_RE = /<[^>]*>/g;
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const FILENAME_TRAVERSAL_RE = /[/\\]/g;
const CONTROL_CHARS_RE = /[\x00-\x08\x0b\x0c\x0e-\x1f]/g;
const MULTI_SPACE_RE = /\s+/g;

export function sanitizeEmail(email: unknown): string | null {
  if (typeof email !== 'string') return null;
  const cleaned = email.trim().toLowerCase().replace(CONTROL_CHARS_RE, '');
  if (cleaned.length > MAX_EMAIL_LEN) return null;
  if (!EMAIL_RE.test(cleaned)) return null;
  return cleaned;
}

export function sanitizeString(input: unknown, maxLen = MAX_TEXT_LEN): string | null {
  if (typeof input !== 'string') return null;
  let cleaned = input.replace(HTML_TAG_RE, '').replace(CONTROL_CHARS_RE, '');
  cleaned = cleaned.trim().replace(MULTI_SPACE_RE, ' ');
  if (cleaned.length > maxLen) return null;
  return cleaned;
}

export function validatePassword(password: unknown): string | null {
  if (typeof password !== 'string') return null;
  if (password.length < MIN_PASSWORD_LEN || password.length > MAX_PASSWORD_LEN) return null;
  return password;
}

export function validateAction<T extends string>(action: string, allowed: readonly T[]): T | null {
  if (allowed.includes(action as T)) return action as T;
  return null;
}

export function sanitizeFilename(name: unknown): string | null {
  if (typeof name !== 'string') return null;
  const cleaned = name.replace(FILENAME_TRAVERSAL_RE, '_').replace(CONTROL_CHARS_RE, '');
  if (cleaned.length > 255) return null;
  return cleaned || null;
}

export function validateFileType(file: File, allowedTypes: readonly string[]): boolean {
  return allowedTypes.includes(file.type);
}

export function validateFileSize(file: File, maxBytes = MAX_FILE_SIZE): boolean {
  return file.size <= maxBytes && file.size > 0;
}

export function validatePositiveInt(val: unknown): number | null {
  if (typeof val === 'string') {
    const n = parseInt(val, 10);
    if (!isNaN(n) && n > 0 && n <= Number.MAX_SAFE_INTEGER) return n;
  }
  if (typeof val === 'number' && Number.isInteger(val) && val > 0) return val;
  return null;
}

export function safeJsonParse(input: unknown): unknown {
  if (typeof input !== 'string') return null;
  try {
    return JSON.parse(input);
  } catch {
    return null;
  }
}

export function apiError(status: number, message: string) {
  return json({ success: false, error: message }, { status });
}

export function sanitizeForDisplay(input: string, maxLen = 500): string {
  let cleaned = input.replace(HTML_TAG_RE, '').replace(CONTROL_CHARS_RE, '');
  cleaned = cleaned.trim().replace(MULTI_SPACE_RE, ' ');
  if (cleaned.length > maxLen) cleaned = cleaned.slice(0, maxLen) + '...';
  return cleaned;
}
