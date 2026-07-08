/**
 * UI-HARD-1100 — Approving Authority read-only review package (pack §16, doc §16).
 *
 * Route (Desk): `/desk/tenders/{tender_code}/approval-review`.
 * APIs: GET approval-review-package; POST approve/return/reject — wired by host.
 */

import { useCallback, useMemo, useState, type ReactElement } from "react";

import { ActionAwareButton, BlockerList, ReadinessStatusBadge } from "../../shared";

import type {
	ApprovalReturnForCorrectionPayload,
	ApprovalReviewPackageScreenProps,
} from "./approvalReviewPackageScreen.types";

function ReadonlyLines({ lines }: { lines: string[] }): ReactElement {
	return (
		<ul className="list-unstyled small" style={{ marginBottom: 0 }}>
			{lines.map((line, i) => (
				<li key={i}>{line}</li>
			))}
		</ul>
	);
}

export function ApprovalReviewPackageScreen(props: ApprovalReviewPackageScreenProps): ReactElement {
	const {
		tenderCode,
		tenderSummaryLines,
		packageReferenceLines,
		stdTemplateProfileSummary,
		readinessStatus,
		readinessNarrative,
		bundlePreviewText,
		outputSummaryLines,
		boqSummaryLines,
		worksRequirementsSummaryLines,
		warningsBlockers,
		auditEvidenceSummaryLines,
		decisionHistoryLines,
		approveAction,
		returnAction,
		rejectAction,
		requestClarificationAction,
		reasonCodeOptions,
		criticalityOptions,
	} = props;

	const [reasonCode, setReasonCode] = useState("");
	const [comment, setComment] = useState("");
	const [affectedArea, setAffectedArea] = useState("");
	const [criticality, setCriticality] = useState("");
	const [returnFieldErrors, setReturnFieldErrors] = useState<Partial<Record<keyof ApprovalReturnForCorrectionPayload, string>>>(
		{},
	);

	const { onReturnConfirmed, ...returnActionForButton } = returnAction;

	const validateReturn = useCallback((): ApprovalReturnForCorrectionPayload | null => {
		const next: Partial<Record<keyof ApprovalReturnForCorrectionPayload, string>> = {};
		if (!reasonCode.trim()) {
			next.reason_code = "Reason code is required.";
		}
		if (!comment.trim()) {
			next.comment = "Comment is required.";
		}
		if (!affectedArea.trim()) {
			next.affected_area = "Affected area is required.";
		}
		if (!criticality.trim()) {
			next.criticality = "Criticality is required.";
		}
		setReturnFieldErrors(next);
		if (Object.keys(next).length > 0) {
			return null;
		}
		return {
			reason_code: reasonCode.trim(),
			comment: comment.trim(),
			affected_area: affectedArea.trim(),
			criticality: criticality.trim(),
		};
	}, [reasonCode, comment, affectedArea, criticality]);

	const handleReturnAllowed = useCallback(() => {
		const payload = validateReturn();
		if (!payload) {
			return;
		}
		onReturnConfirmed(payload);
	}, [onReturnConfirmed, validateReturn]);

	const reasonOpts = useMemo(
		() =>
			reasonCodeOptions.map((o) => (
				<option key={o.value} value={o.value}>
					{o.label}
				</option>
			)),
		[reasonCodeOptions],
	);
	const critOpts = useMemo(
		() =>
			criticalityOptions.map((o) => (
				<option key={o.value} value={o.value}>
					{o.label}
				</option>
			)),
		[criticalityOptions],
	);

	return (
		<div data-testid="approval-review-page" className="std-engine-approval-review-page">
			<header className="std-engine-approval-review-page__header">
				<h1 className="h2">Approval review</h1>
				<p className="text-muted small">Tender {tenderCode}</p>
			</header>

			<div
				data-testid="approval-review-readonly-banner"
				className="alert alert-info"
				role="status"
				style={{ marginBottom: "1rem" }}
			>
				This package is read-only except approval decision controls. TDS, SCC, BOQ, works requirements, drawings, and
				generated outputs cannot be edited here (doc §16.5).
			</div>

			<p data-testid="approval-edit-boq-control-absent" className="text-muted small" style={{ marginBottom: "1rem" }}>
				No BOQ line editor, quantity grid, or supplier-rate inputs are shown on this review screen.
			</p>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-tender-summary">
				<h2 id="ar-tender-summary" className="h4">
					Tender summary
				</h2>
				<ReadonlyLines lines={tenderSummaryLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-package">
				<h2 id="ar-package" className="h4">
					Package reference
				</h2>
				<ReadonlyLines lines={packageReferenceLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-std">
				<h2 id="ar-std" className="h4">
					STD template / profile
				</h2>
				<ReadonlyLines lines={stdTemplateProfileSummary} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-readiness">
				<h2 id="ar-readiness" className="h4">
					Readiness result
				</h2>
				<div style={{ marginBottom: "0.5rem" }}>
					<ReadinessStatusBadge status={readinessStatus} />
				</div>
				<p className="small" style={{ marginBottom: 0 }}>
					{readinessNarrative}
				</p>
			</section>

			<section
				data-testid="approval-review-bundle-preview"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ar-bundle"
			>
				<h2 id="ar-bundle" className="h4">
					Bundle preview
				</h2>
				<pre className="small" style={{ maxHeight: "12rem", overflow: "auto", marginBottom: 0, whiteSpace: "pre-wrap" }}>
					{bundlePreviewText}
				</pre>
			</section>

			<section
				data-testid="approval-review-output-summaries"
				className="panel panel-default"
				style={{ padding: "0.75rem", marginBottom: "0.75rem" }}
				aria-labelledby="ar-outputs"
			>
				<h2 id="ar-outputs" className="h4">
					Output summaries
				</h2>
				<ReadonlyLines lines={outputSummaryLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-boq">
				<h2 id="ar-boq" className="h4">
					BOQ summary
				</h2>
				<ReadonlyLines lines={boqSummaryLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-works">
				<h2 id="ar-works" className="h4">
					Works requirements summary
				</h2>
				<ReadonlyLines lines={worksRequirementsSummaryLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-warn">
				<h2 id="ar-warn" className="h4">
					Warnings / blockers
				</h2>
				<BlockerList blockers={warningsBlockers} emptyHint="No warnings or blockers." listDataTestId="approval-review-blocker-list" />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-audit">
				<h2 id="ar-audit" className="h4">
					Audit / evidence summary
				</h2>
				<ReadonlyLines lines={auditEvidenceSummaryLines} />
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-history">
				<h2 id="ar-history" className="h4">
					Decision history
				</h2>
				<ol className="small" style={{ marginBottom: 0 }}>
					{decisionHistoryLines.map((line, i) => (
						<li key={i}>{line}</li>
					))}
				</ol>
			</section>

			<section className="panel panel-default" style={{ padding: "0.75rem", marginBottom: "0.75rem" }} aria-labelledby="ar-decisions">
				<h2 id="ar-decisions" className="h4">
					Decision controls
				</h2>
				<p className="text-muted small">Enabled only when action availability allows (SEC-0410).</p>
				<div className="btn-group" style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "0.75rem" }}>
					<ActionAwareButton {...approveAction} buttonTestId="approval-decision-approve" />
					<ActionAwareButton {...returnActionForButton} buttonTestId="approval-decision-return" onAllowedClick={handleReturnAllowed} />
					{rejectAction ? <ActionAwareButton {...rejectAction} buttonTestId="approval-decision-reject" /> : null}
					{requestClarificationAction ? (
						<ActionAwareButton {...requestClarificationAction} buttonTestId="approval-decision-request-clarification" />
					) : null}
				</div>
			</section>

			<form data-testid="approval-return-form" className="panel panel-default" style={{ padding: "0.75rem" }} noValidate>
				<h2 className="h4">Return for correction — required fields</h2>
				<p className="text-muted small">Complete before using &quot;Return for correction&quot; (doc §16.4).</p>
				<div className="form-group">
					<label htmlFor="approval-return-reason_code">reason_code</label>
					<select
						id="approval-return-reason_code"
						className="form-control"
						value={reasonCode}
						onChange={(e) => setReasonCode(e.target.value)}
						aria-invalid={Boolean(returnFieldErrors.reason_code)}
						aria-describedby={returnFieldErrors.reason_code ? "err-reason_code" : undefined}
					>
						<option value="">Select…</option>
						{reasonOpts}
					</select>
					{returnFieldErrors.reason_code ? (
						<p id="err-reason_code" className="text-danger small" role="alert">
							{returnFieldErrors.reason_code}
						</p>
					) : null}
				</div>
				<div className="form-group">
					<label htmlFor="approval-return-comment">comment</label>
					<textarea
						id="approval-return-comment"
						className="form-control"
						rows={3}
						value={comment}
						onChange={(e) => setComment(e.target.value)}
						aria-invalid={Boolean(returnFieldErrors.comment)}
						aria-describedby={returnFieldErrors.comment ? "err-comment" : undefined}
					/>
					{returnFieldErrors.comment ? (
						<p id="err-comment" className="text-danger small" role="alert">
							{returnFieldErrors.comment}
						</p>
					) : null}
				</div>
				<div className="form-group">
					<label htmlFor="approval-return-affected_area">affected_area</label>
					<input
						id="approval-return-affected_area"
						type="text"
						className="form-control"
						value={affectedArea}
						onChange={(e) => setAffectedArea(e.target.value)}
						aria-invalid={Boolean(returnFieldErrors.affected_area)}
						aria-describedby={returnFieldErrors.affected_area ? "err-affected_area" : undefined}
					/>
					{returnFieldErrors.affected_area ? (
						<p id="err-affected_area" className="text-danger small" role="alert">
							{returnFieldErrors.affected_area}
						</p>
					) : null}
				</div>
				<div className="form-group">
					<label htmlFor="approval-return-criticality">criticality</label>
					<select
						id="approval-return-criticality"
						className="form-control"
						value={criticality}
						onChange={(e) => setCriticality(e.target.value)}
						aria-invalid={Boolean(returnFieldErrors.criticality)}
						aria-describedby={returnFieldErrors.criticality ? "err-criticality" : undefined}
					>
						<option value="">Select…</option>
						{critOpts}
					</select>
					{returnFieldErrors.criticality ? (
						<p id="err-criticality" className="text-danger small" role="alert">
							{returnFieldErrors.criticality}
						</p>
					) : null}
				</div>
			</form>
		</div>
	);
}
