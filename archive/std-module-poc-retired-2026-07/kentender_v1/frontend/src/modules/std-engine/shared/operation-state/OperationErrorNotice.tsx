/**
 * UI-HARD-1400 — user-safe error surface (pack §19, doc §19.1).
 *
 * Never renders raw stack traces; uses `safeUserPrimaryMessage`.
 */

import type { ReactElement } from "react";

import { safeUserPrimaryMessage } from "../safeUserMessage";

export type OperationErrorNoticeProps = {
	/** Raw or server message; sanitized before display. */
	message: string;
	resolutionAction?: string;
	referenceCode?: string;
	affectedAreaHref?: string;
	affectedAreaLabel?: string;
};

export function OperationErrorNotice(props: OperationErrorNoticeProps): ReactElement {
	const { message, resolutionAction, referenceCode, affectedAreaHref, affectedAreaLabel } = props;
	const safe = safeUserPrimaryMessage(message);
	const res = (resolutionAction || "").trim();
	const ref = (referenceCode || "").trim();
	const href = (affectedAreaHref || "").trim();
	const linkLabel = (affectedAreaLabel || "").trim() || "View affected area";
	const resolutionCopy = res || "No additional resolution steps were returned for this error.";

	return (
		<div data-testid="operation-error-notice" className="alert alert-danger" role="alert">
			<p style={{ marginBottom: "0.5rem" }}>{safe}</p>
			<p data-testid="operation-resolution-action" className={res ? undefined : "text-muted small"} style={{ marginBottom: href || ref ? "0.5rem" : 0 }}>
				{resolutionCopy}
			</p>
			{href ? (
				<p style={{ marginBottom: ref ? "0.5rem" : 0 }}>
					<a href={href}>{linkLabel}</a>
				</p>
			) : null}
			{ref ? (
				<p className="small text-muted" style={{ marginBottom: 0 }}>
					Reference: <code>{ref}</code>
				</p>
			) : null}
		</div>
	);
}
