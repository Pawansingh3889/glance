"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { CitationChip } from "@/components/CitationChip";
import { DocumentViewer } from "@/components/DocumentViewer";
import { useDocument, useSendDocumentMessage } from "@/lib/queries";
import type { Citation } from "@/lib/types";

export default function DocumentWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const { data: doc, isLoading, error } = useDocument(id);
  const send = useSendDocumentMessage(id);
  const [draft, setDraft] = useState("");
  // Lifted here rather than local to either pane: both the chat's citation chips and
  // the viewer need to read and react to it, and neither is an ancestor of the other.
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [doc?.messages.length, send.isPending]);

  if (isLoading) return <div className="muted">Loading…</div>;
  if (error) return <div className="error-text">{(error as Error).message}</div>;
  if (!doc) return null;

  const ask = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || send.isPending) return;
    setDraft("");
    send.mutate(trimmed);
  };

  return (
    <div className="doc-workspace">
      <div className="doc-workspace-head">
        <button className="link-btn" onClick={() => router.push("/documents")}>
          ← Documents
        </button>
        <h1 className="doc-workspace-title">{doc.title}</h1>
        {doc.extraction_quality != null ? (
          <span className="pill" title="How much of this document could be read confidently">
            {Math.round(doc.extraction_quality * 100)}% read
          </span>
        ) : null}
      </div>

      {doc.status === "failed" ? (
        <div className="error-text">
          Could not read this document{doc.error_message ? `: ${doc.error_message}` : "."}
        </div>
      ) : doc.status !== "ready" ? (
        <div className="muted">Still processing…</div>
      ) : (
        <div className="doc-panes">
          <div className="doc-pane doc-pane-viewer">
            {doc.parsed_content ? (
              <DocumentViewer content={doc.parsed_content} selected={selectedCitation} />
            ) : (
              <div className="muted">Nothing could be read from this document.</div>
            )}
          </div>

          <div className="doc-pane doc-pane-chat">
            <div className="chat-thread">
              {doc.messages.length === 0 ? (
                <div className="muted">Ask a question about this document to get started.</div>
              ) : null}
              {doc.messages.map((message) => (
                <div key={message.id} className={`bubble bubble-${message.role}`}>
                  <div>{message.content}</div>
                  {message.citations.length > 0 ? (
                    <div className="citation-row">
                      {message.citations.map((citation, i) => (
                        <CitationChip
                          key={i}
                          citation={citation}
                          selected={selectedCitation?.quote === citation.quote}
                          onSelect={setSelectedCitation}
                        />
                      ))}
                    </div>
                  ) : null}
                </div>
              ))}
              {send.isPending ? (
                <div className="bubble bubble-assistant typing">
                  <span />
                  <span />
                  <span />
                </div>
              ) : null}
              <div ref={endRef} />
            </div>

            {send.error ? (
              <div className="error-text">{(send.error as Error).message}</div>
            ) : null}

            <form
              className="composer"
              onSubmit={(e) => {
                e.preventDefault();
                ask(draft);
              }}
            >
              <input
                className="field"
                value={draft}
                placeholder="Ask about this document…"
                disabled={send.isPending}
                onChange={(e) => setDraft(e.target.value)}
              />
              <button
                className="btn btn-primary"
                type="submit"
                disabled={send.isPending || !draft.trim()}
              >
                Send
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
