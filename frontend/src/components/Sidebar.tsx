import { useEffect, useState } from "react";
import type { HealthLintResponse, RecentNode, RefactorResponse, StatsResponse } from "../types";

type Props = {
  stats: StatsResponse | null;
  loading: boolean;
  onPickTitle: (title: string) => void;
  onAddNote: () => void;
  onRefactor: () => void;
  onHealthLint: () => void;
  refactorLoading: boolean;
  refactorError: string | null;
  refactorResult: RefactorResponse | null;
  healthLintLoading: boolean;
  healthLintError: string | null;
  healthLintResult: HealthLintResponse | null;
};

function fmtTime(ts: string | undefined): string {
  if (!ts) return "Never";
  const date = new Date(ts);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleString();
}

export function Sidebar({
  stats,
  loading,
  onPickTitle,
  onAddNote,
  onRefactor,
  onHealthLint,
  refactorLoading,
  refactorError,
  refactorResult,
  healthLintLoading,
  healthLintError,
  healthLintResult,
}: Props) {
  const healthCounts = healthLintResult?.counts ?? {};
  const [showRefactorSummary, setShowRefactorSummary] = useState(true);
  const [showHealthSummary, setShowHealthSummary] = useState(true);

  useEffect(() => {
    if (refactorResult) setShowRefactorSummary(true);
  }, [refactorResult]);

  useEffect(() => {
    if (healthLintResult?.report) setShowHealthSummary(true);
  }, [healthLintResult?.report]);

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__logo" aria-hidden>
          <svg viewBox="0 0 24 24" className="sidebar__logo-svg" role="img" aria-label="Wiki Notes logo">
            <circle cx="12" cy="5" r="2.2" />
            <circle cx="5" cy="18" r="2.2" />
            <circle cx="19" cy="18" r="2.2" />
            <path d="M12 7.2L6.6 16.1M12 7.2l5.4 8.9M7.2 18h9.6" />
          </svg>
        </span>
        <div>
          <div className="sidebar__name">WIKI NOTES</div>
        </div>
      </div>

      <button type="button" className="sidebar__add-note" onClick={onAddNote}>
        Ingest
      </button>

      <div className="sidebar__refactor-block">
        <button type="button" className="sidebar__refactor" onClick={onRefactor} disabled={refactorLoading} aria-busy={refactorLoading}>
          {refactorLoading ? "Refactoring..." : "Refactor Knowledge"}
        </button>
        <button type="button" className="sidebar__health" onClick={onHealthLint} disabled={healthLintLoading} aria-busy={healthLintLoading}>
          {healthLintLoading ? "Running Health Lint..." : "Run Health Lint"}
        </button>
        {refactorError ? <p className="sidebar__refactor-error">{refactorError}</p> : null}
        {healthLintError ? <p className="sidebar__refactor-error">{healthLintError}</p> : null}
        {refactorResult && showRefactorSummary ? (
          <div className="sidebar__refactor-summary">
            <button
              type="button"
              className="sidebar__card-close"
              onClick={() => setShowRefactorSummary(false)}
              aria-label="Dismiss refactor summary"
            >
              ×
            </button>
            <div className="sidebar__refactor-summary-title">Refactor complete</div>
            <ul className="sidebar__refactor-list">
              <li className="sidebar__refactor-item">
                <span className="sidebar__refactor-value">{refactorResult.pages_rewritten}</span>
                <span className="sidebar__refactor-label">rewritten</span>
              </li>
              <li className="sidebar__refactor-item">
                <span className="sidebar__refactor-value">{refactorResult.pages_merged}</span>
                <span className="sidebar__refactor-label">merged</span>
              </li>
              <li className="sidebar__refactor-item">
                <span className="sidebar__refactor-value">{refactorResult.pages_updated}</span>
                <span className="sidebar__refactor-label">updated</span>
              </li>
            </ul>
          </div>
        ) : null}
        {healthLintResult?.report && showHealthSummary ? (
          <div className="sidebar__health-summary">
            <button
              type="button"
              className="sidebar__card-close"
              onClick={() => setShowHealthSummary(false)}
              aria-label="Dismiss health lint summary"
            >
              ×
            </button>
            <div className="sidebar__refactor-summary-title">Health lint</div>
            <p className="sidebar__health-time">Last run: {fmtTime(healthLintResult.report.generated_at)}</p>
            <ul className="sidebar__health-counts">
              <li>Contradictions: <strong>{healthCounts.contradictions ?? 0}</strong></li>
              <li>Orphans: <strong>{healthCounts.orphans ?? 0}</strong></li>
              <li>Missing pages: <strong>{healthCounts.missing_pages ?? 0}</strong></li>
            </ul>
            {healthLintResult.next_actions?.length ? (
              <p className="sidebar__health-next">
                Next: {healthLintResult.next_actions[0].action}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>

      <section className="sidebar__section sidebar__section--grow">
        <h3>Recent updates</h3>
        {!stats?.recent_nodes.length ? (
          <p className="sidebar__muted">{loading ? "Loading..." : "No pages yet."}</p>
        ) : (
          <ul className="recent-list">
            {stats.recent_nodes.map((n: RecentNode) => (
              <li key={n.filename}>
                <button type="button" className="recent-list__btn" onClick={() => onPickTitle(n.title)}>
                  <span className="recent-list__title">{n.title}</span>
                  <span className="recent-list__tags">{n.tags.slice(0, 2).join(" · ")}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </section>
    </aside>
  );
}
