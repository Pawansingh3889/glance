"use client";

import { LOCALE_NAMES, LOCALES, useI18n, type Locale } from "@/lib/i18n";

/** A native <select>, deliberately.
 *
 *  A custom dropdown would need its own keyboard handling, focus trap and screen-reader
 *  wiring to match what the platform already gives away — and on the shared floor tablet
 *  this runs on, the native picker is a full-screen list with large targets, which is
 *  better than anything worth hand-building here.
 */
export function LanguageSwitcher({ className = "" }: { className?: string }) {
  const { locale, setLocale, t } = useI18n();

  return (
    <label className={`lang ${className}`.trim()}>
      <span className="sr-only">{t.nav.language}</span>
      <select
        className="lang-select"
        value={locale}
        onChange={(e) => setLocale(e.target.value as Locale)}
      >
        {LOCALES.map((code) => (
          <option key={code} value={code}>
            {LOCALE_NAMES[code]}
          </option>
        ))}
      </select>
    </label>
  );
}
