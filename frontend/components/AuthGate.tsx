"use client";

import { usePathname } from "next/navigation";
import { useSyncExternalStore, type ReactNode } from "react";

import { useAuthStore } from "@/lib/store";

import { CreatorSignIn } from "./CreatorSignIn";
import { GuestGate } from "./GuestGate";

/** Whether persist() has finished reading localStorage.
 *
 *  The token lives in localStorage, which the server cannot see: it renders every visit
 *  as signed out, while the browser may already know otherwise. Deciding from the store
 *  directly would therefore contradict the server's HTML on the very first paint.
 *
 *  useSyncExternalStore is the escape hatch built for exactly this — it renders the
 *  server snapshot (`false`) during hydration, then re-renders with the real one, so
 *  the two passes never disagree. */
function useHydrated(): boolean {
  return useSyncExternalStore(
    (onChange) => useAuthStore.persist.onFinishHydration(onChange),
    () => useAuthStore.persist.hasHydrated(),
    () => false,
  );
}

/** Routes only a survey author can use. Everything else on the site is either public or
 *  something a person on shift does, and asking them for a company account to report a
 *  hazard would mean the hazard goes unreported. */
const CREATOR_PATHS = ["/templates"];

/** Decides *which* door an unauthenticated visitor is shown, not whether there is one.
 *
 *  This used to be a single sign-in screen for everybody, which was wrong in two ways: it
 *  demanded a password from participants who have no account, and — because it replaced
 *  the whole page — there was no way back to the public site once you landed on it. Both
 *  gates below carry a link home. */
export function AuthGate({ children }: { children: ReactNode }) {
  const hydrated = useHydrated();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const pathname = usePathname();

  // Not a spinner: this shows for one frame on a warm load, and a spinner that flashes
  // reads as breakage. A blank shell of the right colour just looks like loading.
  if (!hydrated) return <div className="boot" aria-hidden="true" />;

  // Both, not either: a token we cannot attribute to a user leaves every role gate
  // undecidable, and the pages behind this would render as neither creator nor
  // participant. Signing in again is cheap and correct.
  if (!token || !user) {
    const needsCreator = CREATOR_PATHS.some((path) => pathname.startsWith(path));
    return needsCreator ? <CreatorSignIn /> : <GuestGate />;
  }

  return <>{children}</>;
}
