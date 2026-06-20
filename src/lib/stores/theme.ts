import { writable } from 'svelte/store';

type Theme = 'dark' | 'light' | 'system';

export const theme = writable<Theme>('dark');

export function toggleTheme() {
  theme.update((t) => {
    const next = t === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    return next;
  });
}

export function applyTheme(t: Theme) {
  if (typeof document === 'undefined') return;
  const isDark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.classList.toggle('dark', isDark);
  document.documentElement.classList.toggle('light', !isDark);
}
