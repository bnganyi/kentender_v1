/**
 * UI-HARD-0400 — Configure Tender Document overview (pack §9, doc §8).
 *
 * Procurement Officer entry: tender-oriented labels only; no raw STD mapping surfaces.
 */

import type { ReactElement } from "react";

import { ActionAwareButton, ReadinessStatusBadge } from "../../shared";

import {
	TENDER_CONFIG_OUTPUT_PLAIN_LABEL,
	defaultWorksTenderConfigStages,
	type ConfigureTenderDocumentOverviewPageProps,
	type TenderConfigStageStatus,
} from "./configureTenderDocumentOverview.types";

function stageBadgeClass(status: TenderConfigStageStatus): string {
	switch (status) {
		case "Complete":
			return "label label-success";
		case "Needs Attention":
			return "label label-warning";
		case "Stale":
			return "label label-warning";
		case "Incomplete":
			return "label label-default";
		case "Locked":
			return "label label-info";
		case "Not Applicable":
			return "label label-default";
		case "Not Started":
		default:
			return "label label-default";
	}
}

export function ConfigureTenderDocumentOverviewPage(props: ConfigureTenderDocumentOverviewPageProps): ReactElement {
	const {
		tenderCode,
		tenderTitle,
		packageCode,
		packageTitle,
		contextLines = [],
		selectedStdSummary,
		completionPercent,
		stages: stagesProp,
		outputs,
		readinessStatus,
		readinessDetail,
		nextAction,
	} = props;

	const stages =
		stagesProp === undefined ? defaultWorksTenderConfigStages() : stagesProp;

	const pct = Math.max(0, Math.min(100, Math.round(Number.isFinite(completionPercent) ? completionPercent : 0)));

	return (
		<div data-testid="tender-config-overview-page" className="configure-tender-document-overview-page">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Configure Tender Document</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					Complete tender documents from the approved package and selected standard. This overview shows progress
					and the next step — not internal template engineering screens.
				</p>
			</header>

			<section
				data-testid="tender-config-context-header"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
			>
				<h4 className="h6">Tender and package context</h4>
				<dl className="small" style={{ marginBottom: "0.5rem" }}>
					<dt>Tender</dt>
					<dd>
						<strong>{tenderTitle}</strong> ({tenderCode})
					</dd>
					<dt>Package</dt>
					<dd>
						<strong>{packageTitle}</strong> ({packageCode})
					</dd>
					{contextLines.map((row) => (
						<div key={row.label}>
							<dt>{row.label}</dt>
							<dd>{row.value}</dd>
						</div>
					))}
				</dl>
				<p className="small" style={{ marginBottom: 0 }} role="status" aria-live="polite">
					<strong>Completion progress:</strong> {pct}% complete
				</p>
			</section>

			<section
				data-testid="tender-config-selected-std"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
			>
				<h4 className="h6">Selected standard (template / profile)</h4>
				<p className="small" style={{ marginBottom: 0 }}>
					{selectedStdSummary}
				</p>
			</section>

			<section data-testid="tender-config-stage-list" className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }}>
				<h4 className="h6">Stage statuses</h4>
				{stages.length === 0 ? (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						No stages were provided for this overview.
					</p>
				) : (
					<ul className="list-unstyled small" style={{ marginBottom: 0 }}>
						{stages.map((row) => (
							<li key={row.key} style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.35rem" }}>
								<span style={{ flex: "1 1 auto" }}>{row.label}</span>
								<span className={stageBadgeClass(row.status)} title={row.status}>
									{row.status}
								</span>
							</li>
						))}
					</ul>
				)}
			</section>

			<section
				data-testid="tender-config-output-statuses"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
			>
				<h4 className="h6">Generated output statuses</h4>
				<dl className="small" style={{ marginBottom: 0 }}>
					{outputs.length === 0 ? (
						<p className="text-muted small" style={{ marginBottom: 0 }}>
							No output status rows were supplied.
						</p>
					) : (
						outputs.map((o) => (
							<div key={o.kind} style={{ marginBottom: "0.35rem" }}>
								<dt>{TENDER_CONFIG_OUTPUT_PLAIN_LABEL[o.kind]}</dt>
								<dd style={{ marginBottom: 0 }}>{o.statusLabel}</dd>
							</div>
						))
					)}
				</dl>
			</section>

			<section data-testid="tender-config-readiness-status" style={{ marginBottom: "0.75rem" }}>
				<h4 className="h6">Overall readiness status</h4>
				<p style={{ marginBottom: "0.35rem" }}>
					<ReadinessStatusBadge status={readinessStatus} />
				</p>
				{readinessDetail ? (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						{readinessDetail}
					</p>
				) : null}
			</section>

			<section style={{ marginBottom: "0.75rem" }}>
				<h4 className="h6">Next action</h4>
				{nextAction ? (
					<ActionAwareButton
						actionCode={nextAction.actionCode}
						objectType={nextAction.objectType}
						objectCode={nextAction.objectCode}
						label={nextAction.label}
						variant="primary"
						buttonTestId="tender-config-next-action"
						availabilityContext={nextAction.availabilityContext}
						onAllowedClick={nextAction.onAllowedClick}
					/>
				) : (
					<p className="text-muted small" style={{ marginBottom: 0 }}>
						No primary action is configured for this overview. Use the stage list and workspace links from your host
						application when available.
					</p>
				)}
			</section>
		</div>
	);
}
