import { useMemo, useRef, useState } from "react";

type Props = {
  open: boolean;
  busy: boolean;
  statusText?: string | null;
  error: string | null;
  onClose: () => void;
  onSubmitFiles: (files: File[], generate: boolean) => Promise<string>;
  onSubmitText: (text: string, generate: boolean) => Promise<string>;
};

const ACCEPTED = ".txt,.md,.pdf,.docx";

export function IngestModal({ open, busy, statusText, error, onClose, onSubmitFiles, onSubmitText }: Props) {
  const [files, setFiles] = useState<File[]>([]);
  const [text, setText] = useState("");
  const [toast, setToast] = useState<string | null>(null);
  const [generate, setGenerate] = useState(true);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const hasPayload = files.length > 0 || text.trim().length > 0;
  const subtitle = useMemo(() => `${files.length} file(s) selected`, [files.length]);

  if (!open) return null;

  async function submit() {
    if (!hasPayload || busy) return;
    try {
      let msg = "";
      if (files.length) msg = await onSubmitFiles(files, generate);
      else msg = await onSubmitText(text.trim(), generate);
      setToast(msg);
      window.setTimeout(() => {
        setToast(null);
        setFiles([]);
        setText("");
        onClose();
      }, 1000);
    } catch {
      // Error messaging is handled by parent state and rendered via `error`.
    }
  }

  return (
    <div className="modal-backdrop" role="dialog" aria-modal="true" aria-label="Ingest knowledge modal" onClick={onClose}>
      <div className="modal modal--ingest" onClick={(e) => e.stopPropagation()}>
        <header className="modal__header">
          <h2 className="modal__title">Add Knowledge</h2>
          <button className="modal__close" aria-label="Close ingest modal" onClick={onClose}>
            ×
          </button>
        </header>
        <div className="modal__body">
          <p className="modal__hint modal__hint--ingest">Upload source files or paste notes, then ingest into your knowledge graph.</p>

          <section className="ingest-section">
            <label className="modal__label">Upload files</label>
            <div className="ingest-drop" onClick={() => inputRef.current?.click()} role="button" tabIndex={0}>
              <input
                ref={inputRef}
                type="file"
                hidden
                multiple
                accept={ACCEPTED}
                onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
              />
              <p className="ingest-drop__title">Drop files or click to browse</p>
              <p className="ingest-drop__sub">{subtitle}</p>
            </div>
          </section>
          {!!files.length && (
            <ul className="ingest-file-list">
              {files.map((f) => (
                <li className="ingest-file-list__row" key={`${f.name}-${f.size}`}>
                  <span className="ingest-file-list__name">{f.name}</span>
                  <button
                    className="ingest-drop__clear"
                    onClick={() => setFiles((prev) => prev.filter((x) => x !== f))}
                    aria-label={`Remove ${f.name}`}
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="ingest-divider" aria-hidden>
            <span>OR</span>
          </div>

          <section className="ingest-section">
            <label className="modal__label">Paste note</label>
            <textarea
              className="modal__textarea"
              rows={5}
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder="Paste raw notes..."
            />
          </section>

          <label className="modal__check">
            <input type="checkbox" checked={generate} onChange={(e) => setGenerate(e.target.checked)} />
            Generate wiki after upload
          </label>

          {busy ? (
            <div className="ingest-status">
              <div className="ingest-status__spinner" />
              <span className="ingest-status__text">{statusText || "Processing..."}</span>
            </div>
          ) : null}
          {error ? <p className="modal__error">{error}</p> : null}
          {toast ? <p className="modal__toast modal__toast--success">{toast}</p> : null}

          <div className="modal__actions">
            <button className="modal__btn modal__btn--ghost" onClick={onClose} disabled={busy}>
              Cancel
            </button>
            <button className="modal__btn modal__btn--primary" onClick={submit} disabled={!hasPayload || busy}>
              Ingest
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
