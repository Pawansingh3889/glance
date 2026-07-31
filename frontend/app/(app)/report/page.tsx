"use client";

import Link from "next/link";
import { useState } from "react";

import { useI18n } from "@/lib/i18n";
import { useFileIncident, useIncidentForm } from "@/lib/queries";
import type { IncidentQuestion, IncidentReceipt, IncidentValue } from "@/lib/types";

type Values = Record<string, IncidentValue | undefined>;

/** Whether a question has been answered well enough to submit. Mirrors the backend's
 *  rule rather than replacing it — the server revalidates everything either way; this
 *  only decides when the button lights up. */
function answered(question: IncidentQuestion, value: IncidentValue | undefined): boolean {
  if (value === undefined) return false;
  if (typeof value === "string") return value.trim().length > 0;
  if (Array.isArray(value)) return value.length > 0;
  return true;
}

function Field({
  question,
  value,
  onChange,
}: {
  question: IncidentQuestion;
  value: IncidentValue | undefined;
  onChange: (value: IncidentValue | undefined) => void;
}) {
  const { t, option } = useI18n();
  // A single-select write-in needs two pieces of state — that "somewhere else" is
  // selected, and what was typed — but only ever sends the typed text.
  const [otherPicked, setOtherPicked] = useState(false);
  const name = `q-${question.id}`;

  if (question.answer_type === "yes_no") {
    return (
      <div className="rf-choices">
        {[
          { label: t.report.yes, v: true },
          { label: t.report.no, v: false },
        ].map((choice) => (
          <label key={choice.label} className="rf-choice">
            <input
              type="radio"
              name={name}
              checked={value === choice.v}
              onChange={() => onChange(choice.v)}
            />
            <span>{choice.label}</span>
          </label>
        ))}
      </div>
    );
  }

  if (question.answer_type === "single_select") {
    return (
      <div className="rf-choices rf-choices-stack">
        {question.options.map((opt) => (
          <label key={opt} className="rf-choice">
            <input
              type="radio"
              name={name}
              checked={!otherPicked && value === opt}
              onChange={() => {
                setOtherPicked(false);
                // The English option text is what is sent: the backend validates against
                // the published template, which is English. Only the label is translated.
                onChange(opt);
              }}
            />
            <span>{option(opt)}</span>
          </label>
        ))}
        {question.allow_other ? (
          <>
            <label className="rf-choice">
              <input
                type="radio"
                name={name}
                checked={otherPicked}
                onChange={() => {
                  setOtherPicked(true);
                  onChange("");
                }}
              />
              <span>{t.report.writeIn}</span>
            </label>
            {otherPicked ? (
              <input
                className="field rf-writein"
                placeholder={t.report.writeIn}
                value={typeof value === "string" ? value : ""}
                onChange={(e) => onChange(e.target.value)}
              />
            ) : null}
          </>
        ) : null}
      </div>
    );
  }

  if (question.answer_type === "multi_select") {
    const chosen = Array.isArray(value) ? value : [];
    return (
      <div className="rf-choices rf-choices-stack">
        {question.options.map((opt) => (
          <label key={opt} className="rf-choice">
            <input
              type="checkbox"
              checked={chosen.includes(opt)}
              onChange={(e) =>
                onChange(e.target.checked ? [...chosen, opt] : chosen.filter((c) => c !== opt))
              }
            />
            <span>{option(opt)}</span>
          </label>
        ))}
      </div>
    );
  }

  if (question.answer_type === "long_text") {
    return (
      <textarea
        className="field rf-textarea"
        value={typeof value === "string" ? value : ""}
        onChange={(e) => onChange(e.target.value)}
        placeholder={t.report.freeText}
      />
    );
  }

  if (question.answer_type === "rating") {
    return (
      <div className="rf-choices">
        {[1, 2, 3, 4, 5].map((n) => (
          <label key={n} className="rf-choice">
            <input type="radio" name={name} checked={value === n} onChange={() => onChange(n)} />
            <span>{n}</span>
          </label>
        ))}
      </div>
    );
  }

  return (
    <input
      className="field"
      type={
        question.answer_type === "date"
          ? "date"
          : question.answer_type === "number"
            ? "number"
            : "text"
      }
      value={typeof value === "string" || typeof value === "number" ? String(value) : ""}
      onChange={(e) =>
        onChange(
          question.answer_type === "number"
            ? e.target.value === ""
              ? undefined
              : Number(e.target.value)
            : e.target.value,
        )
      }
    />
  );
}

function Filed({ receipt, onAnother }: { receipt: IncidentReceipt; onAnother: () => void }) {
  const { t } = useI18n();
  return (
    <div className="card rf-filed">
      <p className="rf-filed-tick" aria-hidden="true">
        ✓
      </p>
      <h2>{t.report.filedTitle}</h2>
      <p className="rf-filed-ref">
        {t.report.filedRef} <strong>{receipt.reference}</strong>
      </p>
      <p className="muted rf-filed-note">{t.report.filedNote}</p>
      <div className="page-head-actions rf-filed-actions">
        <button className="btn btn-primary" onClick={onAnother}>
          {t.report.another}
        </button>
        <Link href="/ask" className="btn btn-secondary">
          {t.report.askInstead}
        </Link>
      </div>
    </div>
  );
}

export default function ReportIncident() {
  const { t, question: label, count } = useI18n();
  const { data: form, isLoading, error } = useIncidentForm();
  const file = useFileIncident();
  const [values, setValues] = useState<Values>({});
  const [receipt, setReceipt] = useState<IncidentReceipt | null>(null);

  if (receipt) {
    return (
      <div className="page rf">
        <Filed
          receipt={receipt}
          onAnother={() => {
            setValues({});
            setReceipt(null);
            file.reset();
          }}
        />
      </div>
    );
  }

  if (isLoading) return <div className="muted">{t.common.loading}</div>;
  if (error) return <div className="error-text">{(error as Error).message}</div>;
  if (!form) return null;

  const incomplete = form.questions.filter((q) => q.required && !answered(q, values[q.id]));

  async function onSubmit() {
    if (!form) return;
    const answers = form.questions
      .filter((q) => answered(q, values[q.id]))
      .map((q) => ({ question_id: q.id, value: values[q.id] as IncidentValue }));
    setReceipt(await file.mutateAsync(answers));
  }

  return (
    <div className="page rf">
      <div className="page-head">
        <h1>{t.report.title}</h1>
      </div>
      <p className="rf-lede">{t.report.lede}</p>

      <p className="rf-urgent">{t.report.urgent}</p>

      <div className="rf-fields">
        {form.questions.map((q) => (
          <div key={q.id} className="rf-field card">
            <label className="rf-label">
              {/* Falls back to the API's own wording when a question has no translation —
                  visibly untranslated rather than blank. See lib/i18n/TRANSLATIONS.md. */}
              {label(q.id, q.text)}
              {q.required ? null : <span className="rf-optional">{t.report.optional}</span>}
            </label>
            <Field
              question={q}
              value={values[q.id]}
              onChange={(v) => setValues((prev) => ({ ...prev, [q.id]: v }))}
            />
          </div>
        ))}
      </div>

      {file.error ? (
        <div className="error-text" role="alert">
          {(file.error as Error).message}
        </div>
      ) : null}

      <div className="rf-submit">
        <button
          className="btn btn-primary btn-lg"
          onClick={onSubmit}
          disabled={file.isPending || incomplete.length > 0}
        >
          {file.isPending ? t.report.submitting : t.report.submit}
        </button>
        {incomplete.length > 0 ? (
          <span className="muted">
            {count(t.report.remaining_one, t.report.remaining_other, incomplete.length)}
          </span>
        ) : null}
      </div>
    </div>
  );
}
