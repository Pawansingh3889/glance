import type { Metadata } from "next";

import { AuthGate } from "@/components/AuthGate";
import { TopBar } from "@/components/TopBar";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Survey Service",
  description: "Author and conduct surveys",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          {/* Inside the gate, so the top bar's identity and nav are never rendered for
              a visitor who has not signed in — there would be nothing true to put in
              them. Signed out, the sign-in screen is the whole page. */}
          <AuthGate>
            <TopBar />
            <main className="app-main">{children}</main>
          </AuthGate>
        </Providers>
      </body>
    </html>
  );
}
