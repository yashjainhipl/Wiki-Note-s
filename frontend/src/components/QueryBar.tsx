import { useEffect, useState, type FormEvent } from "react";

import { renderAnswerMarkdown } from "../renderAnswerMarkdown";

const PHRASES = ["Calibrating signal...", "Connecting concepts...", "Traversing active graph...", "Synthesizing cognitive map..."];

type Props = {
  answer: string | null;
  loading: boolean;
  error: string | null;
  answerEpoch: number;
  queryHistory: readonly string[];
  onReplayHistory: (q: string) => void;
  onSubmit: (text: string) => Promise<void> | void;
  onDismissError: () => void;
};

export function QueryBar({ answer, loading, error, answerEpoch, queryHistory, onReplayHistory, onSubmit, onDismissError }: Props) {
  const [value, setValue] = useState("");
  const [phraseIdx, setPhraseIdx] = useState(0);

  useEffect(() => {
    if (!loading) return;
    const id = window.setInterval(() => setPhraseIdx((x) => (x + 1) % PHRASES.length), 1800);
    return () => window.clearInterval(id);
  }, [loading]);

  async function submit(e: FormEvent) {
    e.preventDefault();
    const q = value.trim();
    if (!q || loading) return;
    await onSubmit(q);
    setValue("");
  }

  return (
    <div className={`query-bar${loading ? " query-bar--busy" : ""}`}>
      {queryHistory.length ? (
        <div className="query-bar__history">
          {queryHistory.map((q) => (
            <button key={q} className="query-bar__history-chip" disabled={loading} onClick={() => onReplayHistory(q)}>
              {q}
            </button>
          ))}
        </div>
      ) : null}

      {(loading || error || answer) && (
        <div className="query-bar__panel">
          {loading && <div className="query-bar__thinking">{PHRASES[phraseIdx]}</div>}
          {error && (
            <div className="query-bar__error">
              <div className="query-bar__error-body">{error}</div>
              <button className="query-bar__error-dismiss" onClick={onDismissError} aria-label="Dismiss error">
                ×
              </button>
            </div>
          )}
          {answer && (
            <div className="query-bar__answer" key={answerEpoch}>
              <div className="query-bar__answer-card">
                <div className="query-bar__answer-label">Answer</div>
                <div className="query-bar__answer-text query-bar__answer-text--md">{renderAnswerMarkdown(answer)}</div>
              </div>
            </div>
          )}
        </div>
      )}

      <form className="query-bar__form" onSubmit={submit}>
        <input
          className="query-bar__input"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="QUERY GLOBAL KNOWLEDGE GRAPH..."
          aria-label="Query"
          disabled={loading}
        />
        <button className="query-bar__send" disabled={!value.trim() || loading}>
          Send
        </button>
      </form>
    </div>
  );
}
