"use client";

import { useState } from "react";

import { useFetchDocumentUrl, useUploadDocument } from "@/lib/queries";

/** Upload path first, URL second — upload has no SSRF surface and exercises the whole
 *  pipeline; URL fetching is the guarded, additive extra. Both hand the new document's
 *  id up so the caller can navigate into its workspace. */
export function DocumentUpload({ onUploaded }: { onUploaded: (documentId: string) => void }) {
  const upload = useUploadDocument();
  const fetchUrl = useFetchDocumentUrl();
  const [url, setUrl] = useState("");

  const pending = upload.isPending || fetchUrl.isPending;

  return (
    <div className="card doc-upload">
      <div className="card-label">Discuss a document</div>

      <label className="doc-upload-drop">
        <input
          type="file"
          disabled={pending}
          onChange={(e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (!file) return;
            upload.mutate(file, { onSuccess: (doc) => onUploaded(doc.id) });
          }}
        />
        {upload.isPending ? "Uploading…" : "Choose a file to upload"}
      </label>

      <div className="doc-upload-or">or paste a link</div>

      <form
        className="doc-upload-url"
        onSubmit={(e) => {
          e.preventDefault();
          const trimmed = url.trim();
          if (!trimmed || pending) return;
          fetchUrl.mutate(trimmed, {
            onSuccess: (doc) => {
              setUrl("");
              onUploaded(doc.id);
            },
          });
        }}
      >
        <input
          className="field"
          type="url"
          placeholder="https://…"
          value={url}
          disabled={pending}
          onChange={(e) => setUrl(e.target.value)}
        />
        <button className="btn btn-secondary" type="submit" disabled={pending || !url.trim()}>
          {fetchUrl.isPending ? "Fetching…" : "Fetch"}
        </button>
      </form>

      {upload.error ? <div className="error-text">{(upload.error as Error).message}</div> : null}
      {fetchUrl.error ? (
        <div className="error-text">{(fetchUrl.error as Error).message}</div>
      ) : null}
    </div>
  );
}
