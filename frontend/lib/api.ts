import { useAuthStore } from "./store";
import type {
  AskAnswer,
  AuthToken,
  Credentials,
  GeneratedTemplate,
  Run,
  ResumableRun,
  RunDetail,
  RunSummary,
  RunSummaryContent,
  Template,
  TemplateSummary,
  TemplateVersion,
  TemplateWrite,
  User,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/** Carries the status so callers can tell "you may not" from "it broke". */
export class ApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Our own errors carry `detail` as a string, but FastAPI's request validation returns a
 *  list of `{loc, msg}` instead. Passing that list to Error() stringifies it to
 *  "[object Object]", which is what an author saw for a blank title or a duplicate
 *  option — so flatten it into the field and the reason. */
function errorMessage(body: unknown, fallback: string): string {
  const payload = body as { error?: { message?: unknown }; detail?: unknown } | null;
  const detail = payload?.error?.message ?? payload?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const reasons = detail
      .map((item) => {
        const { loc, msg } = (item ?? {}) as { loc?: unknown; msg?: unknown };
        // Pydantic prefixes custom validators with "Value error, "; it means nothing here.
        const reason = String(msg ?? "").replace(/^Value error, /, "");
        const field = Array.isArray(loc)
          ? loc.filter((part) => part !== "body").join(".")
          : "";
        return field ? `${field}: ${reason}` : reason;
      })
      .filter(Boolean);
    if (reasons.length) return reasons.join("; ");
  }
  return fallback;
}

/** The Authorization header for the signed-in browser, or nothing when signed out.
 *  The backend reads a bearer token and nothing else — it stopped trusting the
 *  `X-User-Id` header this client used to send, and answers requests without one with
 *  a 401 rather than a guess at who is calling. */
function authHeaders(): Record<string, string> {
  const token = useAuthStore.getState().token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** A 401 on a request we *did* authenticate means the token is no longer good —
 *  expired, revoked, or its account deleted. The remedy is always to sign in again, so
 *  clear it and let the auth gate show the sign-in screen. A 401 with no token sent is
 *  an ordinary rejected sign-in attempt and must not be swallowed this way. */
function discardTokenIfRejected(status: number, sentToken: boolean): void {
  if (status === 401 && sentToken) useAuthStore.getState().signOut();
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const auth = authHeaders();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...auth,
    ...((init?.headers as Record<string, string>) ?? {}),
  };

  const res = await fetch(`${BASE}/api/v1${path}`, { ...init, headers });
  if (!res.ok) {
    discardTokenIfRejected(res.status, "Authorization" in auth);
    let message = res.statusText;
    try {
      message = errorMessage(await res.json(), message);
    } catch {
      // non-JSON error body; keep the status text
    }
    throw new ApiError(message, res.status);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

/** For file downloads: same auth header, but the raw Response instead of parsed JSON. */
async function rawRequest(path: string): Promise<Response> {
  const auth = authHeaders();
  const res = await fetch(`${BASE}/api/v1${path}`, { headers: auth });
  if (!res.ok) {
    discardTokenIfRejected(res.status, "Authorization" in auth);
    throw new ApiError(res.statusText, res.status);
  }
  return res;
}

export const api = {
  /** Exchanges email + password for a bearer token. Sends no credentials of its own,
   *  so a 401 here means "wrong email or password" and nothing else. */
  login: (credentials: Credentials) =>
    request<AuthToken>("/auth/login", { method: "POST", body: JSON.stringify(credentials) }),
  /** Who the current token belongs to. The role comes from the database on every call,
   *  so it reflects a promotion or demotion without needing a fresh token. */
  me: () => request<User>("/auth/me"),
  /** Admits a participant with no account. The name is required; the address is contact
   *  detail only and is never used to find or reuse an existing account. */
  startGuest: (display_name: string, email?: string) =>
    request<AuthToken>("/auth/guest", {
      method: "POST",
      body: JSON.stringify(email ? { display_name, email } : { display_name }),
    }),
  listUsers: () => request<User[]>("/users"),
  listTemplates: () => request<TemplateSummary[]>("/templates"),
  getTemplate: (id: string) => request<Template>(`/templates/${id}`),
  createTemplate: (data: TemplateWrite) =>
    request<Template>("/templates", { method: "POST", body: JSON.stringify(data) }),
  updateTemplate: (id: string, data: TemplateWrite) =>
    request<Template>(`/templates/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  deleteTemplate: (id: string) => request<void>(`/templates/${id}`, { method: "DELETE" }),
  publishTemplate: (id: string) =>
    request<TemplateVersion>(`/templates/${id}/publish`, { method: "POST" }),
  generateTemplate: (prompt: string) =>
    request<GeneratedTemplate>("/templates/generate", {
      method: "POST",
      body: JSON.stringify({ prompt }),
    }),
  refineTemplate: (id: string, instruction: string) =>
    request<GeneratedTemplate>(`/templates/${id}/refine`, {
      method: "POST",
      body: JSON.stringify({ instruction }),
    }),
  listPublished: () => request<TemplateSummary[]>("/templates/published"),
  startRun: (templateId: string) =>
    request<Run>("/runs", { method: "POST", body: JSON.stringify({ template_id: templateId }) }),
  getRun: (id: string) => request<Run>(`/runs/${id}`),
  myUnfinishedRuns: () => request<ResumableRun[]>("/runs"),
  sendRunMessage: (id: string, content: string) =>
    request<Run>(`/runs/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) }),
  listTemplateRuns: (templateId: string) => request<RunSummary[]>(`/templates/${templateId}/runs`),
  exportRuns: (templateId: string, format: "csv" | "json") =>
    rawRequest(`/templates/${templateId}/runs/export?format=${format}`),
  getTemplateRun: (templateId: string, runId: string) =>
    request<RunDetail>(`/templates/${templateId}/runs/${runId}`),
  summariseRun: (templateId: string, runId: string, refresh = false) =>
    request<RunSummaryContent>(
      `/templates/${templateId}/runs/${runId}/summary${refresh ? "?refresh=true" : ""}`,
      { method: "POST" },
    ),
  /** One question, one constrained answer. Not a conversation: there is no thread to
   *  resume, so each call stands alone. */
  ask: (question: string, language: string) =>
    request<AskAnswer>("/ask", { method: "POST", body: JSON.stringify({ question, language }) }),
};
