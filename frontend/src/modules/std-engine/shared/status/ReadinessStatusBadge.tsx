/**
 * UI-HARD-0120 — `<ReadinessStatusBadge />` (pack §6, doc §15.3).
 */

import type { ReactElement } from "react";

import type { ReadinessUiStatus } from "./readinessStatus";

export type ReadinessStatusBadgeProps = {
	status: ReadinessUiStatus;
	/** Overrides visible + accessible label (defaults to `status`). */
	label?: string;
};

function badgeClass(status: ReadinessUiStatus): string {
	switch (status) {
		case "Ready":
			return "label label-success";
		case "Blocked":
			return "label label-danger";
		case "Incomplete":
			return "label label-default";
		case "Warning":
			return "label label-warning";
		case "Invalidated":
			return "label label-default";
		default:
			return "label label-default";
	}
}

export function ReadinessStatusBadge(props: ReadinessStatusBadgeProps): ReactElement {
	const { status, label } = props;
	const text = (label || status).trim() || status;
	return (
		<span data-testid="readiness-status-badge" className={badgeClass(status)} title={text}>
			{text}
		</span>
	);
}
