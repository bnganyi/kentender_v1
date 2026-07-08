/**
 * UI-HARD-0120 — `<DenialNotice />` (pack §6, doc §5.4 / §19.2).
 */

import type { ReactElement } from "react";

import { safeUserPrimaryMessage } from "../safeUserMessage";

export type DenialNoticeProps = {
	message: string;
	denialCode?: string | null;
	/** Advanced / audit / admin surfaces only (pack: denial codes visible there only). */
	showDenialCode?: boolean;
};

export function DenialNotice(props: DenialNoticeProps): ReactElement {
	const { message, denialCode, showDenialCode = false } = props;
	const safe = safeUserPrimaryMessage(message);
	const code = (denialCode || "").trim();

	return (
		<div data-testid="denial-notice" className="alert alert-warning std-engine-denial-notice" role="status">
			<p style={{ marginBottom: showDenialCode && code ? "0.35rem" : 0 }}>{safe}</p>
			{showDenialCode && code ? (
				<p className="small text-muted" data-testid="denial-notice-technical-code" style={{ marginBottom: 0 }}>
					<code>{code}</code>
				</p>
			) : null}
		</div>
	);
}
