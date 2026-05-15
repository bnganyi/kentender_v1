/**
 * UI-HARD-0710 — Drawing register / table (pack §13, doc §12).
 *
 * Section VII binding is fixed for drawings; staleness warning uses pack copy.
 */

import { useState, type ChangeEvent, type ReactElement } from "react";

import {
	DRAWING_REGISTER_SECTION_VII_DISPLAY,
	DRAWING_REGISTER_STALENESS_WARNING_PACK,
	EMPTY_DRAWING_REGISTER_DRAFT,
	type DrawingRegisterDraft,
	type DrawingRegisterRow,
	type DrawingRegisterScreenProps,
} from "./drawingRegisterScreen.types";

function mergeDraft(base: DrawingRegisterDraft, patch: Partial<DrawingRegisterDraft>): DrawingRegisterDraft {
	return { ...base, ...patch };
}

export function DrawingRegisterScreen(props: DrawingRegisterScreenProps): ReactElement {
	const { rows, showStalenessWarning = false, draft: controlledDraft, onDraftChange, onAddDrawing } = props;

	const [internalDraft, setInternalDraft] = useState<DrawingRegisterDraft>(EMPTY_DRAWING_REGISTER_DRAFT);
	const isControlled = controlledDraft !== undefined;
	const draft = isControlled ? controlledDraft! : internalDraft;

	const setDraft = (next: DrawingRegisterDraft) => {
		if (isControlled) {
			onDraftChange?.(next);
		} else {
			setInternalDraft(next);
		}
	};

	const patchDraft = (patch: Partial<DrawingRegisterDraft>) => {
		setDraft(mergeDraft(draft, patch));
	};

	const sectionViiCode = "SECTION_VII_DRAWINGS";

	const handleAdd = () => {
		onAddDrawing?.({
			drawing_code: draft.drawing_code.trim(),
			title: draft.title.trim(),
			revision: draft.revision.trim(),
			file_reference: draft.file_reference.trim(),
			section_code: sectionViiCode,
			classification: draft.classification.trim(),
			issue_status: draft.issue_status.trim(),
		});
		if (!isControlled) {
			setInternalDraft(EMPTY_DRAWING_REGISTER_DRAFT);
		}
	};

	return (
		<div data-testid="drawing-register-screen" className="drawing-register-screen">
			<header className="page-head" style={{ marginBottom: "1rem" }}>
				<h2>Drawing register</h2>
				<p className="text-muted small" style={{ marginBottom: 0 }}>
					Drawings are listed in a register with Section VII binding. Replacing or revising a drawing after outputs exist can
					invalidate generated documents — see the warning below when applicable.
				</p>
			</header>

			<div
				data-testid="drawing-section-vii-binding"
				className="alert alert-info"
				role="status"
				style={{ marginBottom: "0.75rem" }}
			>
				<strong>Section binding (fixed):</strong> {DRAWING_REGISTER_SECTION_VII_DISPLAY}. New rows are recorded under this section
				(doc §12.2).
			</div>

			{showStalenessWarning ? (
				<div data-testid="drawing-staleness-warning" className="alert alert-warning" role="alert" style={{ marginBottom: "0.75rem" }}>
					{DRAWING_REGISTER_STALENESS_WARNING_PACK}
				</div>
			) : null}

			<div className="table-responsive" style={{ marginBottom: "1rem" }}>
				<table data-testid="drawing-register-table" className="table table-bordered table-condensed">
					<thead>
						<tr>
							<th scope="col">Drawing Code</th>
							<th scope="col">Title</th>
							<th scope="col">Revision</th>
							<th scope="col">File</th>
							<th scope="col">Status</th>
							<th scope="col">Section</th>
						</tr>
					</thead>
					<tbody>
						{rows.length === 0 ? (
							<tr>
								<td colSpan={6} className="text-muted small">
									No drawings in the register yet. Use “Add drawing” below.
								</td>
							</tr>
						) : (
							rows.map((r) => (
								<tr key={r.id}>
									<td>{r.drawing_code}</td>
									<td>{r.title}</td>
									<td>{r.revision}</td>
									<td>{r.file_reference}</td>
									<td>
										{r.issue_status}
										{r.classification ? (
											<>
												<br />
												<span className="text-muted small">{r.classification}</span>
											</>
										) : null}
									</td>
									<td>{DRAWING_REGISTER_SECTION_VII_DISPLAY}</td>
								</tr>
							))
						)}
					</tbody>
				</table>
			</div>

			<section className="panel panel-default" style={{ padding: "0.75rem" }} aria-label="Add drawing">
				<h4 className="h6" style={{ marginTop: 0 }}>
					Add drawing
				</h4>
				<div className="row">
					<div className="col-md-4">
						<div className="form-group">
							<label className="control-label" htmlFor="drawing-field-code">
								Drawing code
							</label>
							<input
								id="drawing-field-code"
								type="text"
								className="form-control"
								data-testid="drawing-field-code"
								value={draft.drawing_code}
								onChange={(e: ChangeEvent<HTMLInputElement>) => patchDraft({ drawing_code: e.target.value })}
								autoComplete="off"
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label className="control-label" htmlFor="drawing-field-revision">
								Revision
							</label>
							<input
								id="drawing-field-revision"
								type="text"
								className="form-control"
								data-testid="drawing-field-revision"
								value={draft.revision}
								onChange={(e: ChangeEvent<HTMLInputElement>) => patchDraft({ revision: e.target.value })}
								autoComplete="off"
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label className="control-label" htmlFor="drawing-draft-title">
								Title
							</label>
							<input
								id="drawing-draft-title"
								type="text"
								className="form-control"
								value={draft.title}
								onChange={(e: ChangeEvent<HTMLInputElement>) => patchDraft({ title: e.target.value })}
								autoComplete="off"
							/>
						</div>
					</div>
				</div>
				<div className="row">
					<div className="col-md-4">
						<div className="form-group">
							<label className="control-label" htmlFor="drawing-draft-file">
								File reference
							</label>
							<input
								id="drawing-draft-file"
								type="text"
								className="form-control"
								placeholder="Storage key or URL"
								value={draft.file_reference}
								onChange={(e: ChangeEvent<HTMLInputElement>) => patchDraft({ file_reference: e.target.value })}
								autoComplete="off"
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label className="control-label" htmlFor="drawing-draft-classification">
								Classification
							</label>
							<input
								id="drawing-draft-classification"
								type="text"
								className="form-control"
								value={draft.classification}
								onChange={(e: ChangeEvent<HTMLInputElement>) => patchDraft({ classification: e.target.value })}
								autoComplete="off"
							/>
						</div>
					</div>
					<div className="col-md-4">
						<div className="form-group">
							<label className="control-label" htmlFor="drawing-draft-issue">
								Issue status
							</label>
							<input
								id="drawing-draft-issue"
								type="text"
								className="form-control"
								value={draft.issue_status}
								onChange={(e: ChangeEvent<HTMLInputElement>) => patchDraft({ issue_status: e.target.value })}
								autoComplete="off"
							/>
						</div>
					</div>
				</div>
				<button type="button" className="btn btn-primary" data-testid="drawing-add-row" onClick={handleAdd}>
					Add drawing
				</button>
			</section>
		</div>
	);
}
