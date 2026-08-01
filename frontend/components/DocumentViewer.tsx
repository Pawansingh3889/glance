"use client";

import { useEffect, useMemo } from "react";

import type { Citation, ParsedContent } from "@/lib/types";

interface Group {
  heading: string | null;
  page: number | null;
  blocks: { text: string; kind: string }[];
}

/** Groups the flat, per-block section list into headed groups — mirroring the
 *  backend's own render_for_prompt grouping, so what the model was shown and what is
 *  shown here line up. */
function groupSections(content: ParsedContent): Group[] {
  const groups: Group[] = [];
  for (const block of content.sections) {
    const last = groups[groups.length - 1];
    if (last && last.heading === block.heading) {
      last.blocks.push({ text: block.text, kind: block.kind });
    } else {
      groups.push({
        heading: block.heading,
        page: block.page,
        blocks: [{ text: block.text, kind: block.kind }],
      });
    }
  }
  return groups;
}

function anchorId(heading: string | null, index: number): string {
  const slug = (heading ?? "untitled").toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return `doc-section-${index}-${slug}`;
}

/** Does this group contain the passage a citation points at? A citation's `section` is
 *  the model's own label for where it read something, which may not exactly match a
 *  heading string — the quoted text actually appearing in the group is the more
 *  reliable signal, checked first. */
function groupMatches(group: Group, citation: Citation): boolean {
  if (group.blocks.some((b) => b.text.includes(citation.quote))) return true;
  return citation.section != null && citation.section === group.heading;
}

export function DocumentViewer({
  content,
  selected,
}: {
  content: ParsedContent;
  selected: Citation | null;
}) {
  const groups = useMemo(() => groupSections(content), [content]);

  useEffect(() => {
    if (!selected) return;
    const index = groups.findIndex((g) => groupMatches(g, selected));
    if (index < 0) return;
    document
      .getElementById(anchorId(groups[index].heading, index))
      ?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [selected, groups]);

  if (groups.length === 0 && content.tables.length === 0) {
    return <div className="muted">Nothing could be read from this document.</div>;
  }

  return (
    <div className="doc-viewer">
      {groups.map((group, i) => {
        const highlighted = selected != null && groupMatches(group, selected);
        return (
          <section
            key={anchorId(group.heading, i)}
            id={anchorId(group.heading, i)}
            className={highlighted ? "doc-section doc-section-highlight" : "doc-section"}
          >
            {group.heading ? (
              <h3 className="doc-section-heading">
                {group.heading}
                {group.page ? (
                  <span className="doc-section-page"> · page {group.page}</span>
                ) : null}
              </h3>
            ) : null}
            {group.blocks.map((block, j) => (
              <p key={j} className="doc-section-text">
                {block.text}
              </p>
            ))}
          </section>
        );
      })}
      {content.tables.map((table, i) => (
        <section key={`table-${i}`} className="doc-section">
          <h3 className="doc-section-heading">
            Table{table.heading ? ` — ${table.heading}` : ""}
            {table.page ? <span className="doc-section-page"> · page {table.page}</span> : null}
          </h3>
          <pre className="doc-table">{table.markdown}</pre>
        </section>
      ))}
    </div>
  );
}
