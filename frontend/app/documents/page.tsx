"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { DocumentUpload } from "@/components/DocumentUpload";
import { useDocuments } from "@/lib/queries";
import type { DocumentStatus } from "@/lib/types";

const STATUS_LABEL: Record<DocumentStatus, string> = {
  ready: "Ready",
  pending: "Processing…",
  parsing: "Processing…",
  failed: "Could not be read",
};

export default function DocumentsPage() {
  const { data: documents, isLoading, error } = useDocuments();
  const router = useRouter();

  return (
    <div className="page">
      <div className="page-head">
        <h1>Documents</h1>
      </div>

      <DocumentUpload onUploaded={(id) => router.push(`/documents/${id}`)} />

      {isLoading ? <div className="muted">Loading…</div> : null}
      {error ? <div className="error-text">{(error as Error).message}</div> : null}

      <div className="survey-list">
        {documents?.map((doc) => (
          <Link key={doc.id} href={`/documents/${doc.id}`} className="survey-row">
            <div>
              <div className="template-title">{doc.title}</div>
              <div className="template-meta">
                {doc.source_type === "url" ? "Fetched" : "Uploaded"} ·{" "}
                {STATUS_LABEL[doc.status] ?? doc.status}
              </div>
            </div>
          </Link>
        ))}
        {documents && documents.length === 0 ? (
          <div className="muted">No documents yet. Upload one or paste a link above.</div>
        ) : null}
      </div>
    </div>
  );
}
