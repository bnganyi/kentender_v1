/**
 * UI-HARD-0700 — Works requirements as structured component cards (pack §12, doc §11).
 *
 * Uploads require component + section + classification; no generic unbound path for readiness.
 */

import { useMemo, useState, type ChangeEvent, type ReactElement } from "react";

import {
	WORKS_REQUIREMENT_CARD_DEFS,
	type AttachmentClassification,
	type WorksRequirementComponentId,
	type WorksRequirementStatus,
	type WorksRequirementsScreenProps,
} from "./worksRequirementsScreen.types";

const DEFAULT_STATUS: WorksRequirementStatus = "Not Started";

const CLASSIFICATION_OPTIONS: { value: AttachmentClassification; label: string }[] = [
	{ value: "supplier_facing", label: "Supplier Facing" },
	{ value: "internal_only", label: "Internal Only" },
	{ value: "contract_facing", label: "Contract Facing" },
];

function statusBadgeClass(status: WorksRequirementStatus): string {
	switch (status) {
		case "Complete":
			return "label label-success";
		case "Needs Attention":
			return "label label-warning";
		case "Incomplete":
			return "label label-default";
		case "Not Started":
		default:
			return "label label-default";
	}
}

export function WorksRequirementsScreen(props: WorksRequirementsScreenProps): ReactElement {
	const { componentStatuses = {}, readinessNotice, onAttachmentFileChosen } = props;

	const [uploadComponent, setUploadComponent] = useState<WorksRequirementComponentId | "">("");
	const [uploadSection, setUploadSection] = useState("");
	const [uploadClassification, setUploadClassification] = useState<AttachmentClassification | "">("");

	const bindingsComplete = Boolean(uploadComponent && uploadSection.trim() && uploadClassification);
	const showSupplierFacingHint = uploadClassification === "supplier_facing";

	const resolvedStatuses = useMemo(() => {
		const out: Record<WorksRequirementComponentId, WorksRequirementStatus> = {} as Record<
			WorksRequirementComponentId,
			WorksRequirementStatus
		>;
		for (const c of WORKS_REQUIREMENT_CARD_DEFS) {
			out[c.id] = componentStatuses[c.id] ?? DEFAULT_STATUS;
		}
		return out;
	}, [componentStatuses]);

	const defaultReadiness =
		"Generic uploads without component, section, and classification binding do not satisfy readiness (doc §11.2).";

	return (
		<div data-testid="works-requirements-screen" className="works-requirements-screen">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Works requirements</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					Each area is a structured component — not a single bucket for unclassified files. Attachments must name the component,
					section, and audience classification before they can be uploaded here.
				</p>
			</header>

			{readinessNotice === undefined ? (
				<div className="alert alert-info" role="status" style={{ marginBottom: "0.75rem" }}>
					{defaultReadiness}
				</div>
			) : readinessNotice ? (
				<div className="alert alert-warning" role="status" style={{ marginBottom: "0.75rem" }}>
					{readinessNotice}
				</div>
			) : null}

			<div className="row" style={{ marginBottom: "1rem" }}>
				{WORKS_REQUIREMENT_CARD_DEFS.map((card) => {
					const st = resolvedStatuses[card.id];
					return (
						<div className="col-md-6 col-lg-4" key={card.id} style={{ marginBottom: "0.75rem" }}>
							<section
								data-testid={card.sectionTestId}
								className="panel panel-default"
								style={{ padding: "0.75rem", height: "100%" }}
								aria-labelledby={`${card.sectionTestId}-title`}
							>
								<h4 className="h6" id={`${card.sectionTestId}-title`} style={{ marginTop: 0 }}>
									{card.title}
								</h4>
								<p style={{ marginBottom: "0.35rem" }}>
									<span className={statusBadgeClass(st)} title={st}>
										{st}
									</span>
								</p>
								<p className="text-muted small" style={{ marginBottom: 0 }}>
									Use the attachment area below after selecting this component (or another), a section code, and a
									classification.
								</p>
							</section>
						</div>
					);
				})}
			</div>

			<section
				data-testid="works-attachment-upload"
				className="panel panel-default"
				style={{ padding: "0.75rem" }}
				aria-label="Attachment upload with binding"
			>
				<h4 className="h6" style={{ marginTop: 0 }}>
					Add attachment
				</h4>
				<p className="small" style={{ marginBottom: "0.65rem" }}>
					<strong>Required before file choice:</strong> component binding, section binding, and classification (pack §12).
				</p>

				<div className="form-group">
					<label className="control-label" htmlFor="works-attachment-component">
						Component binding
					</label>
					<select
						id="works-attachment-component"
						className="form-control"
						value={uploadComponent}
						onChange={(e: ChangeEvent<HTMLSelectElement>) =>
							setUploadComponent((e.target.value || "") as WorksRequirementComponentId | "")
						}
					>
						<option value="">Select component…</option>
						{WORKS_REQUIREMENT_CARD_DEFS.map((c) => (
							<option key={c.id} value={c.id}>
								{c.title}
							</option>
						))}
					</select>
				</div>

				<div className="form-group">
					<label className="control-label" htmlFor="works-attachment-section">
						Section binding
					</label>
					<input
						id="works-attachment-section"
						type="text"
						className="form-control"
						placeholder="e.g. Section III — Works requirements"
						value={uploadSection}
						onChange={(e) => setUploadSection(e.target.value)}
						autoComplete="off"
					/>
				</div>

				<div className="form-group">
					<label className="control-label" htmlFor="works-attachment-classification">
						Classification
					</label>
					<select
						id="works-attachment-classification"
						data-testid="works-attachment-classification"
						className="form-control"
						value={uploadClassification}
						onChange={(e: ChangeEvent<HTMLSelectElement>) =>
							setUploadClassification((e.target.value || "") as AttachmentClassification | "")
						}
					>
						<option value="">Select classification…</option>
						{CLASSIFICATION_OPTIONS.map((o) => (
							<option key={o.value} value={o.value}>
								{o.label}
							</option>
						))}
					</select>
				</div>

				{showSupplierFacingHint ? (
					<p className="alert alert-info small" role="status" style={{ marginBottom: "0.65rem" }}>
						<strong>Supplier Facing:</strong> this classification is visible in the procurement record; supplier-facing and
						contract-facing attachments affect Bundle and DCM readiness (doc §11.3).
					</p>
				) : null}

				<div className="form-group" style={{ marginBottom: 0 }}>
					<label className="control-label" htmlFor="works-attachment-file">
						File
					</label>
					<input
						id="works-attachment-file"
						type="file"
						className="form-control"
						disabled={!bindingsComplete}
						title={
							bindingsComplete
								? "Choose a file to upload with the selected bindings."
								: "Select component, section, and classification first."
						}
						onChange={(e: ChangeEvent<HTMLInputElement>) => {
							const f = e.target.files?.[0];
							if (f && bindingsComplete && uploadComponent && uploadClassification) {
								onAttachmentFileChosen?.({
									componentId: uploadComponent,
									sectionCode: uploadSection.trim(),
									classification: uploadClassification,
									file: f,
								});
							}
							e.target.value = "";
						}}
					/>
					{!bindingsComplete ? (
						<p className="text-muted small" style={{ marginTop: "0.35rem", marginBottom: 0 }}>
							File choice stays disabled until component, section, and classification are set — generic unbound upload cannot
							satisfy readiness.
						</p>
					) : null}
				</div>
			</section>
		</div>
	);
}
