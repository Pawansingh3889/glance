import type { Metadata } from "next";

import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Harbourline — food safety, HACCP & health and safety surveys",
  description:
    "Audit HACCP critical control points, cold chain integrity and health and safety "
    + "reporting across fish processing and food manufacturing sites.",
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
