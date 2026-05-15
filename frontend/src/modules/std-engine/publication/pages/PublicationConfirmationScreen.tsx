/**
 * UI-HARD-1200 — Publication confirmation (pack §17, doc §17).
 *
 * Route (Desk): `/desk/tenders/{tender_code}/publish`.
 * APIs: `POST /api/tenders/{tender_code}/publish`, action availability — wired by host.
 */

import type { ReactElement } from "react";

import { ActionAwareButton, ReadinessStatusBadge } from "../../shared";

import { PUBLICATION_IMMUTABILITY_WARNING_TEXT } from "./publicationConfirmationScreen.constants";
import type { PublicationConfirmationScreenProps } from "./publicationConfirmationScreen.types";

export function PublicationConfirmationScreen(props: PublicationConfirmationScreenProps): ReactElement {
	const {
		tenderCode,
		approvalStatusLabel,
		approvalReady,
		readinessStatus,
		readinessNarrative,
		readinessReady,
		outputStatuses,
		evidencePackageStatus,
		publicationSnapshotReadiness,
		publishPrerequisitesMet,
		publishPrerequisitesBlockedHint,
		publishAction,
		publicationLastError,
	} = props;

	const blockedHint =
		(publishPrerequisitesBlockedHint || "").trim() ||
		"Approval and readiness must both be satisfied before publish is offered (doc §17).";

	return (
		<div data-testid="publication-page" className="std-engine-publication-page">
			<header style={{ marginBottom: "1rem" }}>
				<h1 className="h2">Publish tender</h1>
				<p className="text-muted small">Tender {tenderCode}</p>
			</header>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pub-approval">
				<h2 id="pub-approval" className="h4">
					Approval status
				</h2>
				<div data-testid="publication-approval-status">
					<p style={{ marginBottom: "0.35rem" }}>{approvalStatusLabel}</p>
					{approvalReady ? (
						<span className="label label-success">Ready to publish (approval)</span>
					) : (
						<span className="label label-warning">Approval not satisfied</span>
					)}
				</div>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pub-readiness">
				<h2 id="pub-readiness" className="h4">
					Readiness status
				</h2>
				<div data-testid="publication-readiness-status">
					<div style={{ marginBottom: "0.35rem" }}>
						<ReadinessStatusBadge status={readinessStatus} />
					</div>
					<p className="small text-muted" style={{ marginBottom: 0 }}>
						{readinessNarrative}
					</p>
					{readinessReady ? null : (
						<p className="small text-warning" style={{ marginTop: "0.35rem", marginBottom: 0 }}>
							Readiness is not in a publish-allowed state.
						</p>
					)}
				</div>
			</section>

			<section
				data-testid="publication-output-statuses"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="pub-outputs"
			>
				<h2 id="pub-outputs" className="h4">
					Output statuses
				</h2>
				<ul className="list-unstyled small" style={{ marginBottom: 0 }}>
					{outputStatuses.map((row, i) => (
						<li key={i}>
							<strong>{row.label}:</strong> {row.statusLine}
						</li>
					))}
				</ul>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pub-evidence">
				<h2 id="pub-evidence" className="h4">
					Evidence package status
				</h2>
				<div data-testid="publication-evidence-status">
					<p style={{ marginBottom: 0 }}>{evidencePackageStatus}</p>
				</div>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="pub-snapshot">
				<h2 id="pub-snapshot" className="h4">
					Publication snapshot readiness
				</h2>
				<p style={{ marginBottom: 0 }}>{publicationSnapshotReadiness}</p>
			</section>

			<div
				data-testid="publication-immutability-warning"
				className="alert alert-warning"
				role="region"
				aria-label="Immutability warning"
				style={{ marginBottom: "0.75rem" }}
			>
				<strong>Legal notice.</strong> {PUBLICATION_IMMUTABILITY_WARNING_TEXT}
			</div>

			{publicationLastError ? (
				<div className="alert alert-danger" role="alert" style={{ marginBottom: "0.75rem" }}>
					<strong>Publication could not complete.</strong> {publicationLastError.message}
					{publicationLastError.resolutionAction ? (
						<p className="small" style={{ marginBottom: 0, marginTop: "0.35rem" }}>
							{publicationLastError.resolutionAction}
						</p>
					) : null}
				</div>
			) : null}

			<section className="panel panel-default" style={{ padding: "0.75rem" }} aria-labelledby="pub-action">
				<h2 id="pub-action" className="h4">
					Publish action
				</h2>
				{!publishPrerequisitesMet ? (
					<div>
						<button type="button" className="btn btn-primary" disabled data-testid="publication-confirm-button">
							{publishAction.label}
						</button>
						<p className="text-muted small" style={{ marginTop: "0.5rem", marginBottom: 0 }}>
							{blockedHint}
						</p>
					</div>
				) : (
					<ActionAwareButton {...publishAction} buttonTestId="publication-confirm-button" variant="primary" />
				)}
			</section>
		</div>
	);
}
