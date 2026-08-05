'use client';

import { useCallback, useEffect, useSyncExternalStore } from 'react';

type ResolvedTheme = 'light' | 'dark';

/**
 * Shared theme state using useSyncExternalStore so all components
 * that call useTheme() share the same resolved value and re-render
 * together when it changes.
 */
let currentTheme: ResolvedTheme = 'light';
const listeners = new Set<() => void>();

function getSnapshot(): ResolvedTheme {
  return currentTheme;
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

function setThemeInternal(next: ResolvedTheme) {
  if (next === currentTheme) return;
  currentTheme = next;

  if (next === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }

  localStorage.setItem('theme', next);
  listeners.forEach((fn) => fn());
}

export function useTheme() {
  const resolvedTheme = useSyncExternalStore(subscribe, getSnapshot, () => 'light' as ResolvedTheme);

  useEffect(() => {
    const stored = localStorage.getItem('theme') as ResolvedTheme | null;
    if (stored === 'dark' || stored === 'light') {
      setThemeInternal(stored);
    } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
      setThemeInternal('dark');
    } else {
      setThemeInternal('light');
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setThemeInternal(currentTheme === 'dark' ? 'light' : 'dark');
  }, []);

  return { resolvedTheme, toggleTheme };
}
