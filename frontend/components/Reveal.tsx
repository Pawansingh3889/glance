"use client";

import { useEffect, useRef, type ReactNode } from "react";

/** Fades and lifts its children in when they first scroll into view.
 *
 *  IntersectionObserver rather than a scroll listener: it does not run on the main thread
 *  for every pixel of scrolling, which is what makes this cheap enough for a low-end
 *  floor tablet.
 *
 *  The visible/hidden state is written straight to the element's class list rather than
 *  held in React state. That is not a shortcut — it is the correct shape: this
 *  synchronises the DOM with an observer, no render depends on it, and putting it in
 *  state would mean calling setState from inside an effect and re-rendering the subtree
 *  on every reveal.
 *
 *  Two things make it safe rather than merely decorative:
 *
 *  - It renders *visible* and is only hidden once the observer is attached, so with
 *    JavaScript disabled or still loading the content is readable rather than
 *    permanently invisible.
 *  - `prefers-reduced-motion` skips the whole thing. Vestibular disorders are why that
 *    media query exists, and a page of sliding panels is what it is meant to prevent.
 */
export function Reveal({
  children,
  delay = 0,
  className = "",
}: {
  children: ReactNode;
  /** Milliseconds to stagger by, for sequences like a row of cards. */
  delay?: number;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;

    node.classList.remove("reveal-in");
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add("reveal-in");
            // Once revealed, stop watching: re-hiding something the reader has already
            // read as they scroll back up is disorienting, not delightful.
            observer.unobserve(entry.target);
          }
        }
      },
      // A small negative bottom margin so the reveal fires just before the element is
      // fully on screen, rather than after the reader is already looking at it.
      { threshold: 0.1, rootMargin: "0px 0px -40px 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`reveal reveal-in ${className}`.trim()}
      style={delay ? { transitionDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
