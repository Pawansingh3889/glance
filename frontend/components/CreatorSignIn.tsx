"use client";

import Link from "next/link";
import { useState } from "react";

import { useI18n } from "@/lib/i18n";
import { ssoConfigured, signInWithMicrosoft } from "@/lib/msal";
import { useSignIn, useSignInWithToken } from "@/lib/queries";

import { LanguageSwitcher } from "./LanguageSwitcher";

/** The five seeded development accounts (backend app/seed.py). Hidden outside
 *  development on purpose: docker-compose.prod.yml does not seed, so advertising them on
 *  a real install would be a lie. They are also the only way in while SSO is
 *  unconfigured, which is why they stay. */
const DEMO_ACCOUNTS = [
  { email: "ava@glance.dev", name: "Ava Whitlock" },
  { email: "arjun@glance.dev", name: "Arjun Rao" },
];
const DEMO_PASSWORD = "glance-dev-password";
const showDemoAccounts = process.env.NODE_ENV !== "production";

/** Sign-in for survey authors and safety leads — roughly a tenth of the people who use
 *  this, and the only ones who need an identity the company vouches for. Everyone else
 *  goes through GuestGate and never sees this screen. */
export function CreatorSignIn() {
  const { t } = useI18n();
  const withToken = useSignInWithToken();
  const withPassword = useSignIn();
  const [failed, setFailed] = useState<string | null>(null);

  async function onMicrosoft() {
    setFailed(null);
    try {
      const token = await signInWithMicrosoft();
      if (token) withToken.mutate(token);
    } catch (error) {
      setFailed((error as Error).message);
    }
  }

  const busy = withToken.isPending || withPassword.isPending;
  const error = failed ?? (withToken.error as Error | null)?.message ?? null;

  return (
    <div className="gate">
      <div className="gate-card">
        <div className="gate-top">
          <Link href="/" className="gate-back">
            ← {t.guest.back}
          </Link>
          <LanguageSwitcher />
        </div>

        <h1 className="gate-title">{t.sso.title}</h1>
        <p className="gate-sub">{t.sso.body}</p>

        <button
          className="btn btn-primary btn-lg gate-submit gate-ms"
          onClick={onMicrosoft}
          disabled={busy || !ssoConfigured}
        >
          <MicrosoftMark />
          {t.sso.button}
        </button>

        {!ssoConfigured ? (
          <p className="gate-note" role="status">
            {t.sso.unavailable}
          </p>
        ) : null}

        {error ? (
          <div className="error-text" role="alert">
            {error}
          </div>
        ) : null}

        {showDemoAccounts ? (
          <div className="gate-demo">
            <div className="gate-demo-label">Development accounts</div>
            <div className="gate-demo-list">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  className="chip"
                  disabled={busy}
                  onClick={() =>
                    withPassword.mutate({ email: account.email, password: DEMO_PASSWORD })
                  }
                >
                  {account.name}
                </button>
              ))}
            </div>
            {withPassword.error ? (
              <div className="error-text" role="alert">
                {(withPassword.error as Error).message}
              </div>
            ) : null}
          </div>
        ) : null}

        <p className="gate-note gate-note-quiet">
          {t.sso.notYou}{" "}
          <Link href="/report" className="qa-link">
            {t.nav.report}
          </Link>
        </p>
      </div>
    </div>
  );
}

/** The four-square mark. Inline rather than an image so it needs no network request and
 *  inherits nothing from the theme — these are Microsoft's brand colours and must not
 *  shift with ours. */
function MicrosoftMark() {
  return (
    <svg width="16" height="16" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <rect x="0" y="0" width="7" height="7" fill="#f25022" />
      <rect x="9" y="0" width="7" height="7" fill="#7fba00" />
      <rect x="0" y="9" width="7" height="7" fill="#00a4ef" />
      <rect x="9" y="9" width="7" height="7" fill="#ffb900" />
    </svg>
  );
}
