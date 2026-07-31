"use client";

import { createContext, useContext, useEffect, useMemo, useSyncExternalStore, type ReactNode } from "react";

import { bg } from "./dictionaries/bg";
import { en, type Dictionary } from "./dictionaries/en";
import { es } from "./dictionaries/es";
import { lt } from "./dictionaries/lt";
import { lv } from "./dictionaries/lv";
import { pl } from "./dictionaries/pl";
import { pt } from "./dictionaries/pt";
import { ro } from "./dictionaries/ro";
import { DEFAULT_LOCALE, detectLocale, isLocale, type Locale } from "./locales";

const DICTIONARIES: Record<Locale, Dictionary> = { en, pl, lt, ro, pt, es, lv, bg };

const STORAGE_KEY = "glance.locale";

/* ── the locale, as an external store ─────────────────────────────────────────────
 *
 * The chosen language lives in localStorage, which the server cannot see: it renders
 * every visit in the default language while the browser may already know better.
 * Resolving that with useState + useEffect would mean setting state inside an effect —
 * a cascading render, and what React's lint rule is warning about.
 *
 * useSyncExternalStore is the tool built for this, and the same one AuthGate uses for
 * the token: it renders the server snapshot during hydration, then re-renders with the
 * real one, so the two passes never disagree. */

let current: Locale | null = null;
const listeners = new Set<() => void>();

function clientSnapshot(): Locale {
  // Resolved once, lazily, on first read in the browser. Cached because
  // useSyncExternalStore calls this on every render and re-reading localStorage each
  // time would be wasteful.
  if (current === null) {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    current = stored && isLocale(stored) ? stored : detectLocale(navigator.languages ?? []);
  }
  return current;
}

/** What the server renders, and what the client renders during hydration. */
function serverSnapshot(): Locale {
  return DEFAULT_LOCALE;
}

function subscribe(onChange: () => void): () => void {
  listeners.add(onChange);
  return () => {
    listeners.delete(onChange);
  };
}

function writeLocale(next: Locale): void {
  current = next;
  window.localStorage.setItem(STORAGE_KEY, next);
  for (const listener of listeners) listener();
}

/* ── context ─────────────────────────────────────────────────────────────────── */

interface I18n {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Dictionary;
  /** The wording for an incident question, falling back to whatever the API returned.
   *
   *  This fallback is deliberate and is not the "silent default" the codebase forbids
   *  elsewhere: showing the English question is strictly better than a blank or a key,
   *  and it is what happens when the template is republished with new questions. */
  question: (id: string, fallback: string) => string;
  /** Likewise for a select option, keyed by its English text. */
  option: (text: string) => string;
  /** Fills {n} and picks the singular or plural form. */
  count: (one: string, other: string, n: number) => string;
}

const I18nContext = createContext<I18n | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const locale = useSyncExternalStore(subscribe, clientSnapshot, serverSnapshot);

  // Kept in step with <html lang> so screen readers announce in the right language and
  // the browser offers the right hyphenation and spell-checking. Updating an external
  // system from React state is what an effect is actually for.
  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const value = useMemo<I18n>(() => {
    const t = DICTIONARIES[locale];
    return {
      locale,
      setLocale: writeLocale,
      t,
      question: (id, fallback) => t.questions[id] ?? fallback,
      option: (text) => t.options[text] ?? text,
      count: (one, other, n) => (n === 1 ? one : other).replace("{n}", String(n)),
    };
  }, [locale]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18n {
  const value = useContext(I18nContext);
  // Loudly, rather than silently returning English: a component rendering outside the
  // provider would otherwise look translated in development and never change language.
  if (value === null) throw new Error("useI18n must be used inside <I18nProvider>");
  return value;
}

export type { Dictionary };
export { LOCALES, LOCALE_NAMES, type Locale } from "./locales";
