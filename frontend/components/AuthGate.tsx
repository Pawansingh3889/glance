"use client";

import { useSyncExternalStore, type ReactNode } from "react";

import { useAuthStore } from "@/lib/store";

import { SignIn } from "./SignIn";

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

/** Decides whether the app is reachable at all. Signed out, the sign-in screen is the
 *  whole page — there is no version of these screens that works without a token. */
export function AuthGate({ children }: { children: ReactNode }) {
  const hydrated = useHydrated();
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);

  // Not a spinner: this shows for one frame on a warm load, and a spinner that flashes
  // reads as breakage. A blank shell of the right colour just looks like loading.
  if (!hydrated) return <div className="boot" aria-hidden="true" />;

  // Both, not either: a token we cannot attribute to a user leaves every role gate
  // undecidable, and the pages behind this would render as neither creator nor
  // participant. Signing in again is cheap and correct.
  if (!token || !user) return <SignIn />;

  return <>{children}</>;
}
