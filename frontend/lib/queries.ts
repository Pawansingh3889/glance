"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "./api";
import { useAuthStore } from "./store";
import type { Credentials, RunDetail, TemplateWrite } from "./types";

/** The signed-in user's id, or null. Every query below is keyed on it so one account's
 *  cached data can never be shown to the next one after a sign-out and sign-in. */
export function useCurrentUserId(): string | null {
  return useAuthStore((s) => s.user?.id ?? null);
}

/** The signed-in user's record (id + role), for role-gating nav and pages. Read from
 *  the auth store rather than fetched, so a page can decide what to render on its first
 *  paint instead of flashing the wrong role's view while a request is in flight. */
export function useCurrentUser() {
  return useAuthStore((s) => s.user);
}

/** Sign in, then immediately resolve who the token belongs to. The role is never taken
 *  from the login response — the backend decides it, and /auth/me is where it says so. */
export function useSignIn() {
  const qc = useQueryClient();
  const signIn = useAuthStore((s) => s.signIn);
  return useMutation({
    mutationFn: async (credentials: Credentials) => {
      const { access_token } = await api.login(credentials);
      // Set the token first: api.me() reads it out of the store for its own header.
      useAuthStore.setState({ token: access_token });
      try {
        return { token: access_token, user: await api.me() };
      } catch (error) {
        // Never leave a token behind that we could not identify. It would look signed
        // in and 401 on every page.
        useAuthStore.getState().signOut();
        throw error;
      }
    },
    onSuccess: ({ token, user }) => {
      // Drop whatever the previous account cached before the new one renders.
      qc.clear();
      signIn(token, user);
    },
  });
}

export function useSignOut() {
  const qc = useQueryClient();
  const signOut = useAuthStore((s) => s.signOut);
  return () => {
    signOut();
    qc.clear();
  };
}

export function useTemplates() {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["templates", userId],
    queryFn: api.listTemplates,
    enabled: !!userId,
  });
}

export function useTemplate(id: string) {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["template", id, userId],
    queryFn: () => api.getTemplate(id),
    enabled: !!userId,
  });
}

export function useCreateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateWrite) => api.createTemplate(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function useUpdateTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateWrite) => api.updateTemplate(id, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useDeleteTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.deleteTemplate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function usePublishTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.publishTemplate(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function useGenerateTemplate() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (prompt: string) => api.generateTemplate(prompt),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["templates"] }),
  });
}

export function useRefineTemplate(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (instruction: string) => api.refineTemplate(id, instruction),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["template", id] });
      qc.invalidateQueries({ queryKey: ["templates"] });
    },
  });
}

export function usePublishedSurveys() {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["published-surveys", userId],
    queryFn: api.listPublished,
    enabled: !!userId,
  });
}

export function useRun(id: string) {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["run", id, userId],
    queryFn: () => api.getRun(id),
    enabled: !!userId,
  });
}

export function useStartRun() {
  return useMutation({ mutationFn: (templateId: string) => api.startRun(templateId) });
}

export function useTemplateRuns(templateId: string) {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["template-runs", templateId, userId],
    queryFn: () => api.listTemplateRuns(templateId),
    enabled: !!userId,
  });
}

export function useTemplateRun(templateId: string, runId: string | null) {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["template-run", templateId, runId, userId],
    queryFn: () => api.getTemplateRun(templateId, runId as string),
    enabled: !!userId && !!runId,
  });
}

/** Summarising is a model call the author asks for, so it is a mutation, not a query
 *  that fires on render. The result is written back into the cached run detail. */
export function useSummariseRun(templateId: string, runId: string | null) {
  const qc = useQueryClient();
  const userId = useCurrentUserId();
  return useMutation({
    mutationFn: (refresh: boolean = false) =>
      api.summariseRun(templateId, runId as string, refresh),
    onSuccess: (summary) =>
      qc.setQueryData(["template-run", templateId, runId, userId], (run: RunDetail | undefined) =>
        run ? { ...run, summary } : run,
      ),
  });
}

/** The respondent's own unfinished runs, so the home can offer Continue. */
export function useMyUnfinishedRuns() {
  const userId = useCurrentUserId();
  return useQuery({
    queryKey: ["my-runs", userId],
    queryFn: api.myUnfinishedRuns,
    enabled: !!userId,
  });
}

export function useSendRunMessage(id: string) {
  const qc = useQueryClient();
  const userId = useCurrentUserId();
  return useMutation({
    mutationFn: (content: string) => api.sendRunMessage(id, content),
    // The turn returns the whole updated run, so seed the cache rather than refetch it.
    onSuccess: (run) => qc.setQueryData(["run", id, userId], run),
  });
}

/** Ask the shop-floor assistant a question. A mutation rather than a query: it is an
 *  action the user takes, it spends provider tokens, and it must never be re-run
 *  automatically on a refocus or a retry. */
export function useAsk() {
  return useMutation({
    mutationFn: ({ question, language }: { question: string; language: string }) =>
      api.ask(question, language),
  });
}

/** Admit a participant who has no account. Mirrors useSignIn's token handling exactly —
 *  the token is only kept once we can say who it belongs to. */
export function useStartGuest() {
  const qc = useQueryClient();
  const signIn = useAuthStore((s) => s.signIn);
  return useMutation({
    mutationFn: async ({ name, email }: { name: string; email?: string }) => {
      const { access_token } = await api.startGuest(name, email);
      useAuthStore.setState({ token: access_token });
      try {
        return { token: access_token, user: await api.me() };
      } catch (error) {
        useAuthStore.getState().signOut();
        throw error;
      }
    },
    onSuccess: ({ token, user }) => {
      qc.clear();
      signIn(token, user);
    },
  });
}

/** Adopt a token an identity provider issued. Unlike useSignIn there are no credentials
 *  to exchange — MSAL has already done that — so this only has to establish who the
 *  token belongs to, which the backend answers from the token itself. */
export function useSignInWithToken() {
  const qc = useQueryClient();
  const signIn = useAuthStore((s) => s.signIn);
  return useMutation({
    mutationFn: async (accessToken: string) => {
      useAuthStore.setState({ token: accessToken });
      try {
        return { token: accessToken, user: await api.me() };
      } catch (error) {
        // A token we cannot attribute is worse than none: it looks signed in and 401s
        // on every page.
        useAuthStore.getState().signOut();
        throw error;
      }
    },
    onSuccess: ({ token, user }) => {
      qc.clear();
      signIn(token, user);
    },
  });
}
