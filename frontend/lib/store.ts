import { create } from "zustand";
import { persist } from "zustand/middleware";

import type { User } from "./types";

interface AuthState {
  /** The bearer token from POST /auth/login. The API client reads it out of band for
   *  the Authorization header on every request. */
  token: string | null;
  /** The signed-in account, captured at sign-in from GET /auth/me. Held alongside the
   *  token so role gates and query keys can be answered synchronously, without every
   *  page waiting on a round trip before it can decide what to render. */
  user: User | null;
  signIn: (token: string, user: User) => void;
  signOut: () => void;
}

// Persisted, so a reload keeps you signed in. Nothing here is a secret the browser did
// not already hold: the token is what authenticates this browser, and localStorage is
// where it has to live for a reload to survive at all.
//
// This store is read during render *and* imperatively by lib/api.ts. Anything deciding
// what to render must read it through the hook, so a sign-in or sign-out re-renders.
export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      signIn: (token, user) => set({ token, user }),
      signOut: () => set({ token: null, user: null }),
    }),
    { name: "glance-auth" },
  ),
);

interface DraftNoteState {
  pending: Record<string, string>;
  setPendingNote: (templateId: string, note: string) => void;
  clearPendingNote: (templateId: string) => void;
}

// Hands the generation note from the home page to the builder across the navigation
// that opens the fresh draft. Ephemeral (not persisted): the builder reads it once at
// mount and clears it so it doesn't re-seed on a later visit.
export const useDraftNoteStore = create<DraftNoteState>((set) => ({
  pending: {},
  setPendingNote: (templateId, note) =>
    set((s) => ({ pending: { ...s.pending, [templateId]: note } })),
  clearPendingNote: (templateId) =>
    set((s) => {
      if (!(templateId in s.pending)) return s;
      const next = { ...s.pending };
      delete next[templateId];
      return { pending: next };
    }),
}));
