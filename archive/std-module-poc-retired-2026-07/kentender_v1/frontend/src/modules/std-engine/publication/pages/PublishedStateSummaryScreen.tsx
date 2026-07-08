/**
 * UI-HARD-1210 — Post-publication immutable summary (pack §17 ticket 1210, doc §17.4).
 *
 * Edit actions are not offered here (pack acceptance). Evidence opens read-only export/view target from host.
 */

import type { ReactElement } from "react";

import { PUBLISHED_STATE_LOCK_MESSAGE } from "./publishedStateSummaryScreen.constants";
import type { PublishedStateSummaryScreenProps } from "./publishedStateSummaryScreen.types";

export function PublishedStateSummaryScreen(props: PublishedStateSummaryScreenProps): ReactElement {
	const {
		tenderCode,
		snapshotCode,
		bundleVersion,
		dsmVersion,
		domVersion,
		demVersion,
		dcmVersion,
		evidencePackageHref,
		evidencePackageLinkLabel = "Open evidence package",
		nextLifecycleStep,
		addendumReissueGuidance,
	} = props;

	const linkLabel = evidencePackageLinkLabel.trim() || "Open evidence package";

	return (
		<div data-testid="published-state-summary" className="std-engine-published-state-summary">
			<header style={{ marginBottom: "1rem" }}>
				<h1 className="h2">Published tender</h1>
				<p className="text-muted small">Tender {tenderCode}</p>
			</header>

			<div className="alert alert-success" role="status" style={{ marginBottom: "0.75rem" }}>
				<strong>Status:</strong> Published
			</div>

			<p className="alert alert-info" style={{ marginBottom: "1rem" }}>
				{PUBLISHED_STATE_LOCK_MESSAGE}
			</p>

			<p className="text-muted small" style={{ marginBottom: "1rem" }}>
				This summary is read-only. Configuration, BOQ, works attachments, and generated outputs are not editable after
				publication (doc §17.4).
			</p>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pubsnap-heading">
				<h2 id="pubsnap-heading" className="h4">
					Publication snapshot
				</h2>
				<p style={{ marginBottom: 0 }}>
					<strong>Snapshot code:</strong>{" "}
					<span data-testid="published-snapshot-code">{snapshotCode}</span>
				</p>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pubver-heading">
				<h2 id="pubver-heading" className="h4">
					Published output versions
				</h2>
				<dl className="dl-horizontal small" style={{ marginBottom: 0 }}>
					<dt>Bundle</dt>
					<dd data-testid="published-output-version-bundle">{bundleVersion}</dd>
					<dt>DSM</dt>
					<dd data-testid="published-output-version-dsm">{dsmVersion}</dd>
					<dt>DOM</dt>
					<dd data-testid="published-output-version-dom">{domVersion}</dd>
					<dt>DEM</dt>
					<dd data-testid="published-output-version-dem">{demVersion}</dd>
					<dt>DCM</dt>
					<dd data-testid="published-output-version-dcm">{dcmVersion}</dd>
				</dl>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pubev-heading">
				<h2 id="pubev-heading" className="h4">
					Evidence
				</h2>
				<p style={{ marginBottom: 0 }}>
					<a data-testid="published-evidence-link" href={evidencePackageHref}>
						{linkLabel}
					</a>
				</p>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pubnext-heading">
				<h2 id="pubnext-heading" className="h4">
					Next lifecycle step
				</h2>
				<p style={{ marginBottom: 0 }}>{nextLifecycleStep}</p>
			</section>

			<section
				data-testid="published-addendum-guidance"
				className="panel panel-default"
				style={{ padding: "0.75rem" }}
				aria-labelledby="pubadd-heading"
			>
				<h2 id="pubadd-heading" className="h4">
					Addendum / reissue
				</h2>
				<p style={{ marginBottom: 0 }}>{addendumReissueGuidance}</p>
			</section>
		</div>
	);
}
