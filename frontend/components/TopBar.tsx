"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useI18n } from "@/lib/i18n";
import { useCurrentUser, useSignOut } from "@/lib/queries";

import { LanguageSwitcher } from "./LanguageSwitcher";

/** First letters of the display name, for the identity badge. Two words give two
 *  initials; anything else gives one, because "Remy" as "RE" reads like an acronym. */
function initials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
  return (parts[0]?.[0] ?? "?").toUpperCase();
}

export function TopBar() {
  const user = useCurrentUser();
  const signOut = useSignOut();
  const pathname = usePathname();
  const { t } = useI18n();

  // The nav follows the signed-in role: Build is creator-only on the backend, so
  // offering it to a participant only leads to a 403.
  const isCreator = user?.role === "creator";
  const home = isCreator ? "/templates" : "/respond";

  return (
    <header className="topbar">
      <div className="topbar-left">
        <Link href={home} className="topbar-brand">
          Gla<span>nce</span>
        </Link>
        <nav className="topbar-nav" aria-label="Main">
          {/* Roles don't cross: creators build, participants answer. */}
          {isCreator ? (
            <Link href="/templates" aria-current={pathname === "/templates" ? "page" : undefined}>
              {t.nav.build}
            </Link>
          ) : (
            <Link href="/respond" aria-current={pathname === "/respond" ? "page" : undefined}>
              {t.nav.respond}
            </Link>
          )}
          {/* Ask crosses the role line, unlike Build and Respond: anyone signed in can
              put a question to the assistant. */}
          <Link href="/ask" aria-current={pathname === "/ask" ? "page" : undefined}>
            {t.nav.ask}
          </Link>
        </nav>
      </div>

      <div className="topbar-right">
        <LanguageSwitcher className="lang-dark" />
        {user ? (
          <div className="topbar-user">
            <span className="topbar-avatar" aria-hidden="true">
              {initials(user.display_name)}
            </span>
            <span className="topbar-identity">
              <span className="topbar-name">{user.display_name}</span>
              <span className="topbar-role">{user.role}</span>
            </span>
            <button className="btn btn-ghost" onClick={signOut}>
              {t.nav.signOut}
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
