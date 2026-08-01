"use client";

import type { Citation } from "@/lib/types";

/** Where a citation points, for the chip's label — page and section together when both
 *  are known, whichever one is known otherwise, or nothing (some documents have no
 *  page/section structure to cite at all, e.g. a flat text file). */
function locationLabel(citation: Citation): string | null {
  if (citation.section && citation.page) return `${citation.section} · p.${citation.page}`;
  if (citation.section) return citation.section;
  if (citation.page) return `p.${citation.page}`;
  return null;
}

export function CitationChip({
  citation,
  selected,
  onSelect,
}: {
  citation: Citation;
  selected: boolean;
  onSelect: (citation: Citation) => void;
}) {
  const location = locationLabel(citation);
  return (
    <button
      type="button"
      className={selected ? "chip chip-on citation-chip" : "chip citation-chip"}
      title={citation.quote}
      onClick={() => onSelect(citation)}
    >
      “{citation.quote.length > 60 ? `${citation.quote.slice(0, 60)}…` : citation.quote}”
      {location ? <span className="citation-chip-loc"> — {location}</span> : null}
    </button>
  );
}
