/**
 * UI-HARD-0120 — resolution deep link (pack §6).
 */

import type { ReactElement } from "react";

import { sanitizeDomToken } from "../safeUserMessage";

export type ResolutionActionLinkProps = {
	code: string;
	href: string;
	label: string;
};

export function ResolutionActionLink(props: ResolutionActionLinkProps): ReactElement {
	const { code, href, label } = props;
	const tid = `resolution-action-link-${sanitizeDomToken(code)}`;
	return (
		<a data-testid={tid} className="btn btn-xs btn-default" href={href}>
			{label}
		</a>
	);
}
