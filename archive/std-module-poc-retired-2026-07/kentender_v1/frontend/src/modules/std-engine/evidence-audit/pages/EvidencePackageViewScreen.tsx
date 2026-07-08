/**
 * UI-HARD-1300 — Evidence package view (pack §18 ticket 1300, doc §18.1).
 *
 * Route (Desk): `/desk/tenders/{tender_code}/evidence`.
 * Export availability and execution: SEC-0410 + host APIs (validate/export/export-availability).
 */

import type { ReactElement } from "react";

import { ActionAwareButton } from "../../shared";

import type { EvidencePackageViewScreenProps } from "./evidencePackageViewScreen.types";

function ReadonlyLines({ lines }: { lines: string[] }): ReactElement {
	return (
		<ul className="list-unstyled small" style={{ marginBottom: 0 }}>
			{lines.map((line, i) => (
				<li key={i}>{line}</li>
			))}
		</ul>
	);
}

export function EvidencePackageViewScreen(props: EvidencePackageViewScreenProps): ReactElement {
	const {
		tenderCode,
		packageAndTenderLineage,
		stdTemplateProfileLines,
		stdInstanceLines,
		generatedOutputsLines,
		snapshotsLines,
		approvalDecisionsLines,
		auditEventsLines,
		downstreamConsumptionRefs,
		exportAction,
	} = props;

	return (
		<div data-testid="evidence-page" className="std-engine-evidence-page">
			<header style={{ marginBottom: "1rem" }}>
				<h1 className="h2">Evidence package</h1>
				<p className="text-muted small">Tender {tenderCode}</p>
			</header>

			<section
				data-testid="evidence-lineage"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ev-lineage-heading"
			>
				<h2 id="ev-lineage-heading" className="h4">
					Package and tender lineage
				</h2>
				<ReadonlyLines lines={packageAndTenderLineage} />
			</section>

			<section
				data-testid="evidence-std-template"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ev-std-heading"
			>
				<h2 id="ev-std-heading" className="h4">
					STD template / profile
				</h2>
				<ReadonlyLines lines={stdTemplateProfileLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ev-inst-heading">
				<h2 id="ev-inst-heading" className="h4">
					STD instance
				</h2>
				<ReadonlyLines lines={stdInstanceLines} />
			</section>

			<section
				data-testid="evidence-generated-outputs"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ev-out-heading"
			>
				<h2 id="ev-out-heading" className="h4">
					Generated outputs
				</h2>
				<ReadonlyLines lines={generatedOutputsLines} />
			</section>

			<section
				data-testid="evidence-snapshots"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ev-snap-heading"
			>
				<h2 id="ev-snap-heading" className="h4">
					Snapshots
				</h2>
				<ReadonlyLines lines={snapshotsLines} />
			</section>

			<section
				data-testid="evidence-approval-decisions"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ev-appr-heading"
			>
				<h2 id="ev-appr-heading" className="h4">
					Approval decisions
				</h2>
				<ReadonlyLines lines={approvalDecisionsLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ev-audit-heading">
				<h2 id="ev-audit-heading" className="h4">
					Audit events
				</h2>
				<ReadonlyLines lines={auditEventsLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ev-down-heading">
				<h2 id="ev-down-heading" className="h4">
					Downstream consumption references
				</h2>
				<ReadonlyLines lines={downstreamConsumptionRefs} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem" }} aria-labelledby="ev-exp-heading">
				<h2 id="ev-exp-heading" className="h4">
					Evidence export actions
				</h2>
				<p className="text-muted small">Export is allowed only when action availability permits (SEC-0410).</p>
				<ActionAwareButton {...exportAction} buttonTestId="evidence-export-button" variant="primary" />
			</section>
		</div>
	);
}
