/**
 * UI-HARD-0120 — `<OutputStatusBadge />` (pack §6).
 */

import type { ReactElement } from "react";

import { sanitizeDomToken } from "../safeUserMessage";

export type OutputStatusBadgeProps = {
	outputType: string;
	/** User-facing status line (not a raw engine code). */
	statusLabel: string;
};

export function OutputStatusBadge(props: OutputStatusBadgeProps): ReactElement {
	const { outputType, statusLabel } = props;
	const tid = `output-status-badge-${sanitizeDomToken(outputType)}`;
	const label = statusLabel.trim() || "—";
	return (
		<span data-testid={tid} className="label label-default" title={label}>
			{label}
		</span>
	);
}
