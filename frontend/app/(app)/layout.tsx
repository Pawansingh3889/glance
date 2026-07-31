import { AuthGate } from "@/components/AuthGate";
import { TopBar } from "@/components/TopBar";

/** Everything behind sign-in. Kept as a route group so these screens keep their public
 *  URLs (/templates, /respond, /runs/…) while sharing one gate.
 *
 *  Inside the gate, so the top bar's identity and nav are never rendered for a visitor
 *  who has not signed in — there would be nothing true to put in them. Signed out, the
 *  sign-in screen is the whole page. */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <AuthGate>
      <TopBar />
      <main className="app-main">{children}</main>
    </AuthGate>
  );
}
