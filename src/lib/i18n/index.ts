import { writable, derived } from 'svelte/store';
import en from './en.json';

type DeepRecord = { [key: string]: string | DeepRecord };
type TranslationDict = { [key: string]: string | DeepRecord };

const locales: Record<string, TranslationDict> = { en };

export const locale = writable<string>('en');
export const translations = writable<TranslationDict>(locales['en']);

export function registerLocale(code: string, dict: TranslationDict) {
  locales[code] = dict;
}

export function setLocale(code: string) {
  if (locales[code]) {
    locale.set(code);
    translations.set(locales[code]);
  }
}

function resolve(obj: DeepRecord, path: string): string {
  const keys = path.split('.');
  let current: unknown = obj;
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = (current as DeepRecord)[key];
    } else {
      return path;
    }
  }
  return typeof current === 'string' ? current : path;
}

export function t(path: string, vars?: Record<string, string | number>): string {
  let result = '';
  translations.subscribe((val) => { result = resolve(val as DeepRecord, path); })();
  if (vars) {
    for (const [key, value] of Object.entries(vars)) {
      result = result.replace(`{${key}}`, String(value));
    }
  }
  return result;
}

export const _ = derived(translations, ($translations) => {
  return (path: string, vars?: Record<string, string | number>) => {
    let result = resolve($translations as DeepRecord, path);
    if (vars) {
      for (const [key, value] of Object.entries(vars)) {
        result = result.replace(`{${key}}`, String(value));
      }
    }
    return result;
  };
});
