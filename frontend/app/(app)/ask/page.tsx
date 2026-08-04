"use client";

import { useState } from "react";

import { useI18n } from "@/lib/i18n";
import { useAsk } from "@/lib/queries";

export default function Ask() {
  const { t, locale } = useI18n();
  const ask = useAsk();
  const [question, setQuestion] = useState("");
  const [asked, setAsked] = useState("");

  function submit(text: string) {
    const trimmed = text.trim();
    if (!trimmed) return;
    setAsked(trimmed);
    // The interface language is also the answer language: someone reading the page in
    // Lithuanian does not want the answer in English.
    ask.mutate({ question: trimmed, language: locale });
  }

  const answer = ask.data;

  return (
    <div className="page qa">
      <div className="page-head">
        <h1>{t.ask.title}</h1>
      </div>
      <p className="qa-lede">
        {t.ask.lede} {t.ask.disclaimer}
      </p>

      <div className="card qa-box">
        <textarea
          className="qa-input"
          placeholder={t.ask.placeholder}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            // Enter sends; Shift+Enter is a newline. A question is usually one line.
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              submit(question);
            }
          }}
        />
        <div className="qa-actions">
          <span className="qa-hint">{t.ask.hint}</span>
          <button
            className="btn btn-ai"
            onClick={() => submit(question)}
            disabled={ask.isPending || !question.trim()}
          >
            {ask.isPending ? t.ask.thinking : `✦ ${t.ask.send}`}
          </button>
        </div>
      </div>

      {!answer && !ask.isPending && !ask.error ? (
        <div className="qa-examples">
          <p className="card-label">{t.ask.tryTitle}</p>
          <div className="qa-chips">
            {t.ask.examples.map((example) => (
              <button
                key={example}
                className="chip qa-chip"
                onClick={() => {
                  setQuestion(example);
                  submit(example);
                }}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      {ask.isPending ? (
        <div className="card qa-pending">
          <p className="muted">{t.ask.pending}</p>
        </div>
      ) : null}

      {ask.error ? (
        <div className="error-text" role="alert">
          {(ask.error as Error).message}
        </div>
      ) : null}

      {answer ? (
        <article className={`card qa-answer${answer.in_scope ? "" : " qa-answer-off"}`}>
          <header className="qa-answer-head">
            <span className="qa-topic">{t.topics[answer.topic]}</span>
            <p className="qa-asked">{asked}</p>
          </header>
          {/* The model returns prose; blank lines are its paragraph breaks. Rendered as
              separate elements rather than injected as HTML. */}
          {answer.answer
            .split(/\n{2,}/)
            .map((para) => para.trim())
            .filter(Boolean)
            .map((para, i) => (
              <p key={i} className="qa-para">
                {para}
              </p>
            ))}
          {answer.caveat ? <p className="qa-caveat">{answer.caveat}</p> : null}
        </article>
      ) : null}
    </div>
  );
}
