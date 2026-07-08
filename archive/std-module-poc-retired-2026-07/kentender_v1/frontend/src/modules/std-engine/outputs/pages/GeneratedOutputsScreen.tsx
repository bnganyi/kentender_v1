/**
 * UI-HARD-0900 — Generated outputs cards (pack §14, doc §14).
 *
 * Outputs are read-only here; generate-all is SEC-0410–driven. Prohibited actions are not offered.
 */

import type { ReactElement } from "react";

import { ActionAwareButton } from "../../shared";

import {
	GENERATED_OUTPUT_CARD_TITLE,
	GENERATED_OUTPUT_KIND_ORDER,
	type GeneratedOutputKind,
	type GeneratedOutputsScreenProps,
} from "./generatedOutputsScreen.types";

function cardTestId(kind: GeneratedOutputKind): string {
	return `output-card-${kind}`;
}

function staleLabel(stale: boolean): string {
	return stale ? "Stale" : "Current";
}

function staleClass(stale: boolean): string {
	return stale ? "label label-warning" : "label label-success";
}

export function GeneratedOutputsScreen(props: GeneratedOutputsScreenProps): ReactElement {
	const {
		contextTitle,
		outputs,
		generateAllAction,
		onPreview,
		onDownload,
		onViewSummary,
		traceabilityAllowed = false,
		onViewTraceability,
	} = props;

	return (
		<div data-testid="generated-outputs-screen" className="generated-outputs-screen">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Generated outputs</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					{contextTitle} — Bundle, DSM, DOM, DEM, and DCM are generated artefacts. They are not manually edited here; use
					regeneration and upstream business fields (doc §14).
				</p>
			</header>

			<section style={{ marginBottom: "0.75rem" }}>
				<ActionAwareButton
					actionCode={generateAllAction.actionCode}
					objectType={generateAllAction.objectType}
					objectCode={generateAllAction.objectCode}
					label="Generate all outputs"
					variant="primary"
					buttonTestId="output-generate-all-button"
					availabilityContext={generateAllAction.availabilityContext}
					onAllowedClick={generateAllAction.onAllowedClick}
				/>
			</section>

			<div className="row">
				{GENERATED_OUTPUT_KIND_ORDER.map((kind) => {
					const o = outputs[kind];
					const title = GENERATED_OUTPUT_CARD_TITLE[kind];
					return (
						<div className="col-md-6 col-lg-4" key={kind} style={{ marginBottom: "0.75rem" }}>
							<section
								data-testid={cardTestId(kind)}
								className="panel panel-default"
								style={{ padding: "0.75rem", height: "100%" }}
							>
								<h4 className="h6" style={{ marginTop: 0 }}>
									{title}
								</h4>
								{o ? (
									<dl className="small" style={{ marginBottom: "0.5rem" }}>
										<dt>Status</dt>
										<dd>{o.status}</dd>
										<dt>Version</dt>
										<dd>{o.version}</dd>
										<dt>Generated at</dt>
										<dd>{o.generatedAt}</dd>
										<dt>Stale / current</dt>
										<dd>
											<span className={staleClass(o.stale)} title={staleLabel(o.stale)}>
												{staleLabel(o.stale)}
											</span>
										</dd>
										{o.sourceSnapshot ? (
											<>
												<dt>Source snapshot</dt>
												<dd>{o.sourceSnapshot}</dd>
											</>
										) : null}
									</dl>
								) : (
									<p className="text-muted small" style={{ marginBottom: "0.5rem" }}>
										Not generated yet.
									</p>
								)}
								<div className="btn-group-vertical btn-group-sm" style={{ width: "100%" }}>
									<button type="button" className="btn btn-default" onClick={() => onPreview?.(kind)} disabled={!onPreview}>
										Preview
									</button>
									<button type="button" className="btn btn-default" onClick={() => onDownload?.(kind)} disabled={!onDownload}>
										Download
									</button>
									<button type="button" className="btn btn-default" onClick={() => onViewSummary?.(kind)} disabled={!onViewSummary}>
										View summary
									</button>
									{traceabilityAllowed ? (
										<button
											type="button"
											className="btn btn-default"
											onClick={() => onViewTraceability?.(kind)}
											disabled={!onViewTraceability}
										>
											View traceability
										</button>
									) : null}
								</div>
							</section>
						</div>
					);
				})}
			</div>

			<div
				data-testid="output-manual-edit-button-absent"
				className="alert alert-info small"
				role="status"
				style={{ marginTop: "0.5rem" }}
				aria-label="Manual edit of generated outputs is not available on this screen"
			>
				<strong>No manual legal edits:</strong> manual edit of generated outputs, add evaluation criterion, add submission
				requirement, and override contract term are intentionally not offered here (pack prohibited actions).
			</div>
		</div>
	);
}
