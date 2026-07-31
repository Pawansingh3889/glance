"use client";

import { PublicClientApplication, type AuthenticationResult } from "@azure/msal-browser";

/** Microsoft Entra sign-in, for survey authors and safety leads.
 *
 *  Inert until configured. Both values come from the Entra app registration and are
 *  public by design — a client id and a tenant id are not secrets, which is why they can
 *  live in NEXT_PUBLIC_* vars. The security is in the backend's verification of the
 *  resulting token (see backend/app/auth/tokens.py), not in hiding these.
 *
 *  Nothing here decides what anyone may do. It obtains a token; the backend checks its
 *  signature, issuer and audience, and decides who the bearer is.
 */
const CLIENT_ID = process.env.NEXT_PUBLIC_AZURE_CLIENT_ID ?? "";
const TENANT_ID = process.env.NEXT_PUBLIC_AZURE_TENANT_ID ?? "";

/** The scope the API's own app registration exposes. Asking for the right scope is what
 *  makes Entra mint a token whose `aud` is this API rather than Microsoft Graph — a
 *  Graph token would be signed correctly and rejected by the backend's audience check. */
const API_SCOPE = process.env.NEXT_PUBLIC_AZURE_API_SCOPE ?? `api://${CLIENT_ID}/.default`;

export const ssoConfigured = Boolean(CLIENT_ID && TENANT_ID);

let app: PublicClientApplication | null = null;

async function client(): Promise<PublicClientApplication> {
  if (!ssoConfigured) throw new Error("Microsoft sign-in is not configured.");
  if (app === null) {
    app = new PublicClientApplication({
      auth: {
        clientId: CLIENT_ID,
        authority: `https://login.microsoftonline.com/${TENANT_ID}`,
        redirectUri: window.location.origin,
      },
      // sessionStorage rather than localStorage: a shared floor tablet should not keep
      // a manager signed in for the next person who picks it up.
      cache: { cacheLocation: "sessionStorage" },
    });
    await app.initialize();
  }
  return app;
}

/** Sign in and return an access token for this API, or null if the user cancelled. */
export async function signInWithMicrosoft(): Promise<string | null> {
  const msal = await client();
  let result: AuthenticationResult;
  try {
    // Popup rather than redirect: a redirect would unmount the app mid-flow and needs a
    // handleRedirectPromise dance on every page load to pick the result back up.
    result = await msal.loginPopup({ scopes: [API_SCOPE] });
  } catch (error) {
    // A closed popup is a decision, not a failure — say nothing and let them try again.
    if (String(error).includes("user_cancelled")) return null;
    throw error;
  }
  return result.accessToken || null;
}

export async function signOutFromMicrosoft(): Promise<void> {
  if (!ssoConfigured || app === null) return;
  // Clears only this app's cached account. Deliberately not a full logoutRedirect: that
  // signs the person out of every Microsoft session in the browser, which is not what
  // "sign out of Harbourline" should mean.
  const account = app.getAllAccounts()[0];
  if (account) app.clearCache({ account });
}
