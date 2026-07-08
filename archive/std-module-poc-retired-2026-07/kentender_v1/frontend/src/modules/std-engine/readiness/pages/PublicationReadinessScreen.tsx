import { ActionAwareButton, ReadinessStatusBadge } from "../../shared";
import type { PublicationReadinessScreenProps } from "./publicationReadinessScreen.types";

/**
 * Publication readiness (doc §15, pack #15).
 * APIs: POST/GET `/api/tenders/{tender_code}/publication-readiness` — wired by host.
 */
export function PublicationReadinessScreen({
  tenderCode,
  overallStatus,
  criticalBlockers,
  warnings,
  completionCategories,
  outputStatuses,
  evidenceReadinessSummary,
  runReadinessAction,
  nextAction,
}: PublicationReadinessScreenProps) {
  return (
    <div data-testid="readiness-screen" className="std-engine-readiness-screen">
      <header className="std-engine-readiness-screen__header">
        <h1 className="std-engine-readiness-screen__title">Publication readiness</h1>
        <p className="std-engine-readiness-screen__meta">Tender {tenderCode}</p>
        <ActionAwareButton {...runReadinessAction} buttonTestId="readiness-run-button" />
      </header>

      <section className="std-engine-readiness-screen__section" aria-labelledby="readiness-overall-heading">
        <h2 id="readiness-overall-heading">Overall readiness status</h2>
        <div data-testid="readiness-overall-status">
          <ReadinessStatusBadge status={overallStatus} />
        </div>
      </section>

      <section
        className="std-engine-readiness-screen__section"
        aria-labelledby="readiness-blockers-heading"
        data-testid="readiness-critical-blockers"
      >
        <h2 id="readiness-blockers-heading">Critical blockers</h2>
        {criticalBlockers.length === 0 ? (
          <p className="std-engine-readiness-screen__empty">None</p>
        ) : (
          <ul className="std-engine-readiness-screen__blocker-list">
            {criticalBlockers.map((b, i) => (
              <li key={i} className="std-engine-readiness-screen__blocker-card">
                <p>
                  <strong>Blocker:</strong> {b.message}
                </p>
                <p>
                  <strong>Affected area:</strong> {b.affectedArea}
                </p>
                <p>
                  <strong>Why it matters:</strong> {b.whyItMatters}
                </p>
                <p>
                  <strong>Fix:</strong> {b.resolutionAction}
                </p>
                {b.stageLinkHref ? (
                  <p>
                    <a href={b.stageLinkHref}>{b.stageLinkLabel ?? "Go to completion stage"}</a>
                  </p>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        className="std-engine-readiness-screen__section"
        aria-labelledby="readiness-warnings-heading"
        data-testid="readiness-warnings"
      >
        <h2 id="readiness-warnings-heading">Warnings</h2>
        {warnings.length === 0 ? (
          <p className="std-engine-readiness-screen__empty">None</p>
        ) : (
          <ul>
            {warnings.map((w, i) => (
              <li key={i}>{w.message}</li>
            ))}
          </ul>
        )}
      </section>

      <section className="std-engine-readiness-screen__section" aria-labelledby="readiness-categories-heading">
        <h2 id="readiness-categories-heading">Completion categories</h2>
        {completionCategories.length === 0 ? (
          <p className="std-engine-readiness-screen__empty">None</p>
        ) : (
          <ul>
            {completionCategories.map((c) => (
              <li key={c.id}>
                {c.label} — {c.status}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section
        className="std-engine-readiness-screen__section"
        aria-labelledby="readiness-outputs-heading"
        data-testid="readiness-output-statuses"
      >
        <h2 id="readiness-outputs-heading">Generated output statuses</h2>
        {outputStatuses.length === 0 ? (
          <p className="std-engine-readiness-screen__empty">None</p>
        ) : (
          <ul className="std-engine-readiness-screen__output-list">
            {outputStatuses.map((o, i) => (
              <li key={i} className={o.stale ? "std-engine-readiness-screen__output-row--stale" : undefined}>
                <strong>{o.outputLabel}</strong>
                {o.stale ? (
                  <span className="std-engine-readiness-screen__stale-badge" title="Stale output">
                    {" "}
                    STALE
                  </span>
                ) : null}
                <span className="std-engine-readiness-screen__output-status"> — {o.statusLine}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="std-engine-readiness-screen__section" aria-labelledby="readiness-evidence-heading">
        <h2 id="readiness-evidence-heading">Evidence readiness</h2>
        <p>{evidenceReadinessSummary}</p>
      </section>

      <section className="std-engine-readiness-screen__section" aria-labelledby="readiness-next-heading">
        <h2 id="readiness-next-heading">Next action</h2>
        {nextAction ? (
          <ActionAwareButton {...nextAction} buttonTestId="readiness-next-action" />
        ) : (
          <p className="std-engine-readiness-screen__empty">No suggested action</p>
        )}
      </section>
    </div>
  );
}
