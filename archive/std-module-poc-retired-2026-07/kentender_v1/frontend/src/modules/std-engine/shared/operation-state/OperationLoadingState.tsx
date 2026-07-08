/**
 * UI-HARD-1400 — long-running operation feedback (pack §19, doc §19.3).
 */

import type { ReactElement } from "react";

export type OperationLoadingStateProps = {
	/** e.g. "Publishing tender…" */
	label: string;
	/** 0–100 for determinate bar; omit for indeterminate / striped activity. */
	progressPercent?: number | null;
};

export function OperationLoadingState(props: OperationLoadingStateProps): ReactElement {
	const { label, progressPercent } = props;
	const determinate = typeof progressPercent === "number" && !Number.isNaN(progressPercent);
	const pct = determinate ? Math.max(0, Math.min(100, progressPercent as number)) : null;

	return (
		<div
			data-testid="operation-loading-state"
			className="alert alert-info"
			role="status"
			aria-live="polite"
			aria-busy="true"
		>
			<p style={{ marginBottom: "0.5rem" }}>{label}</p>
			{determinate ? (
				<progress value={pct ?? undefined} max={100} style={{ width: "100%", height: "0.75rem" }}>
					{pct}%
				</progress>
			) : (
				<div className="progress" style={{ marginBottom: 0 }}>
					<div
						className="progress-bar progress-bar-striped active"
						style={{ width: "100%" }}
						role="progressbar"
						aria-label={label}
						aria-valuetext="In progress"
					>
						<span className="sr-only">In progress</span>
					</div>
				</div>
			)}
		</div>
	);
}
