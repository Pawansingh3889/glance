"use client";

import Link from "next/link";

import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import { Reveal } from "@/components/Reveal";
import { useI18n } from "@/lib/i18n";

/** The public front door.
 *
 *  Deliberately short. The previous version explained six standards, three steps, a
 *  statistics band and a panel of sample findings — none of which the two people this
 *  page actually serves need. They are: someone who has to answer a survey or ask
 *  something, and an author who needs to sign in. Everything here is one of those two,
 *  and nothing else earned its place.
 */
export default function Landing() {
  const { t } = useI18n();

  return (
    <div className="lp">
      <header className="lp-nav">
        <div className="lp-nav-in">
          <Link href="/" className="lp-brand" aria-label="Glance">
            <span className="lp-mark" aria-hidden="true" />
            Gla<span>nce</span>
          </Link>
          <div className="lp-nav-cta">
            <LanguageSwitcher />
            <Link href="/templates" className="lp-btn lp-btn-ghost">
              {t.nav.signIn}
            </Link>
          </div>
        </div>
      </header>

      <main>
        <section className="lp-hero">
          <div className="lp-hero-in">
            <Reveal>
              <p className="lp-eyebrow">{t.landing.eyebrow}</p>
              <h1>{t.landing.heroTitle}</h1>
              <p className="lp-lede">{t.landing.heroBody}</p>
            </Reveal>

            <Reveal delay={120}>
              <div className="lp-hero-actions">
                <Link href="/respond" className="lp-btn lp-btn-hazard lp-btn-lg">
                  {t.landing.respondCta}
                </Link>
                <Link href="/ask" className="lp-btn lp-btn-outline lp-btn-lg">
                  {t.landing.askCta}
                </Link>
              </div>
            </Reveal>
          </div>
        </section>

        {/* The only other thing the page says: which of the two doors is yours. */}
        <section className="lp-paths">
          <div className="lp-paths-in">
            <Reveal className="lp-path">
              <div className="lp-path-card">
                <span className="lp-path-tag lp-path-tag-floor">{t.landing.staffTitle}</span>
                <p className="lp-path-body">{t.landing.staffBody}</p>
                <div className="lp-path-links">
                  <Link href="/respond" className="lp-inline-link">
                    {t.landing.respondCta} →
                  </Link>
                  <Link href="/ask" className="lp-inline-link">
                    {t.landing.askCta} →
                  </Link>
                </div>
              </div>
            </Reveal>

            <Reveal delay={100} className="lp-path">
              <div className="lp-path-card">
                <span className="lp-path-tag">{t.landing.managerTitle}</span>
                <p className="lp-path-body">{t.landing.managerBody}</p>
                <div className="lp-path-links">
                  <Link href="/templates" className="lp-inline-link">
                    {t.landing.managerCta} →
                  </Link>
                </div>
              </div>
            </Reveal>
          </div>
        </section>
      </main>

      <footer className="lp-foot">
        <div className="lp-foot-in">
          <p className="lp-brand lp-brand-foot">
            <span className="lp-mark" aria-hidden="true" />
            Gla<span>nce</span>
          </p>
          <p className="lp-foot-note">{t.landing.footerNote}</p>
        </div>
      </footer>
    </div>
  );
}
