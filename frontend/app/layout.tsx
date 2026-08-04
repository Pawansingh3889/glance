import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Glance — conversational surveys",
  description:
    "Build a survey by describing it, then let people answer it in a conversation "
    + "rather than a form — on any device, in their own language.",
};

/** The root layout is deliberately unauthenticated: the marketing page at "/" has to be
 *  reachable by someone with no account. Everything that needs a signed-in user lives
 *  under the (app) route group, whose layout carries the gate and the top bar. */
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
