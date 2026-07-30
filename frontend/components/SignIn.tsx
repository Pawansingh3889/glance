"use client";

import { useState } from "react";

import { useSignIn } from "@/lib/queries";

/** The five seeded development accounts, all sharing one password (see the backend's
 *  app/seed.py and the README). Offered as one-click fills because switching between a
 *  creator and a participant is the single most common thing anyone does while working
 *  on this app, and typing the same address twenty times is friction with no purpose.
 *
 *  Hidden outside development on purpose: docker-compose.prod.yml does not seed, so on
 *  a real install these accounts do not exist and advertising them would be a lie. */
const DEMO_ACCOUNTS = [
  { email: "ava@glance.dev", name: "Ava Whitlock", role: "creator" },
  { email: "arjun@glance.dev", name: "Arjun Rao", role: "creator" },
  { email: "rosa@glance.dev", name: "Rosa Bell", role: "participant" },
  { email: "ravi@glance.dev", name: "Ravi Nair", role: "participant" },
  { email: "remy@glance.dev", name: "Remy Fontaine", role: "participant" },
];
const DEMO_PASSWORD = "glance-dev-password";
const showDemoAccounts = process.env.NODE_ENV !== "production";

export function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const signIn = useSignIn();

  const canSubmit = email.trim() !== "" && password !== "" && !signIn.isPending;

  return (
    <div className="signin">
      <div className="signin-card">
        <div className="signin-brand">
          Survey <span>Service</span>
        </div>
        <h1 className="signin-title">Sign in</h1>
        <p className="signin-sub">
          Creators build and publish surveys. Participants answer them.
        </p>

        <form
          className="signin-form"
          onSubmit={(e) => {
            e.preventDefault();
            if (canSubmit) signIn.mutate({ email: email.trim(), password });
          }}
        >
          <label className="signin-field">
            <span>Email</span>
            <input
              className="field"
              type="email"
              autoComplete="username"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
            />
          </label>

          <label className="signin-field">
            <span>Password</span>
            <input
              className="field"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
            />
          </label>

          {/* role="alert" so a screen reader announces the rejection; without it the
              only feedback is a visual change the user may never be told about. */}
          {signIn.error ? (
            <div className="error-text" role="alert">
              {(signIn.error as Error).message}
            </div>
          ) : null}

          <button className="btn btn-primary signin-submit" type="submit" disabled={!canSubmit}>
            {signIn.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>

        {showDemoAccounts ? (
          <div className="signin-demo">
            <div className="signin-demo-label">Development accounts</div>
            <div className="signin-demo-list">
              {DEMO_ACCOUNTS.map((account) => (
                <button
                  key={account.email}
                  type="button"
                  className="chip"
                  disabled={signIn.isPending}
                  onClick={() => {
                    setEmail(account.email);
                    setPassword(DEMO_PASSWORD);
                  }}
                >
                  {account.name}
                  <span className="chip-role">{account.role}</span>
                </button>
              ))}
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
