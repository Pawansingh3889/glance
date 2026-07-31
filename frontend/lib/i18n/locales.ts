/** The languages the floor is served in.
 *
 *  Chosen for UK fish and food processing, where a large share of line staff do not read
 *  English comfortably. Codes are ISO 639-1 and match the backend's AnswerLanguage enum
 *  exactly, so one choice drives both the interface and the language the assistant
 *  answers in.
 */
export const LOCALES = ["en", "pl", "lt", "ro", "pt", "es", "lv", "bg"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "en";

/** Each language named in itself. A switcher that lists "Polish" is useless to someone
 *  who is looking for "Polski". */
export const LOCALE_NAMES: Record<Locale, string> = {
  en: "English",
  pl: "Polski",
  lt: "Lietuvių",
  ro: "Română",
  pt: "Português",
  es: "Español",
  lv: "Latviešu",
  bg: "Български",
};

export function isLocale(value: string): value is Locale {
  return (LOCALES as readonly string[]).includes(value);
}

/** Best match for what the browser asks for, falling back to English.
 *
 *  Matches on the primary subtag only: pt-BR and pt-PT both land on pt, which is right
 *  here — the difference does not change whether someone can read a hazard instruction. */
export function detectLocale(languages: readonly string[]): Locale {
  for (const tag of languages) {
    const primary = tag.toLowerCase().split("-")[0];
    if (isLocale(primary)) return primary;
  }
  return DEFAULT_LOCALE;
}
