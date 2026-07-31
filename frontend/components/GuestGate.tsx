"use client";

import Link from "next/link";
import { useState } from "react";

import { useI18n } from "@/lib/i18n";
import { useStartGuest } from "@/lib/queries";

import { LanguageSwitcher } from "./LanguageSwitcher";

/** What a participant meets instead of a sign-in screen.
 *
 *  A name, and an address only if they want to give one. No password, because there is no
 *  account: someone who has just watched a tote land next to a colleague's foot should not
 *  be asked to register before they can say so.
 */
export function GuestGate() {
  const { t } = useI18n();
  const start = useStartGuest();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");

  const canSubmit = name.trim() !== "" && !start.isPending;

  return (
    <div className="gate">
      <div className="gate-card">
        <div className="gate-top">
          <Link href="/" className="gate-back">
            ← {t.guest.back}
          </Link>
          <LanguageSwitcher />
        </div>

        <h1 className="gate-title">{t.guest.title}</h1>
        <p className="gate-sub">{t.guest.body}</p>

        <form
          className="gate-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) {
              start.mutate({ name: name.trim(), email: email.trim() || undefined });
            }
          }}
        >
          <label className="gate-field">
            <span>{t.guest.nameLabel}</span>
            <input
              className="field"
              autoComplete="name"
              autoFocus
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t.guest.namePlaceholder}
              required
            />
          </label>

          <label className="gate-field">
            <span>
              {t.guest.emailLabel}
              <em className="gate-optional">{t.guest.emailOptional}</em>
            </span>
            <input
              className="field"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="—"
            />
            <small className="gate-help">{t.guest.emailHelp}</small>
          </label>

          {/* role="alert" so a screen reader announces the failure rather than leaving
              it as a purely visual change. */}
          {start.error ? (
            <div className="error-text" role="alert">
              {(start.error as Error).message}
            </div>
          ) : null}

          <button className="btn btn-primary btn-lg gate-submit" type="submit" disabled={!canSubmit}>
            {start.isPending ? t.guest.submitting : t.guest.submit}
          </button>
        </form>
      </div>
    </div>
  );
}
