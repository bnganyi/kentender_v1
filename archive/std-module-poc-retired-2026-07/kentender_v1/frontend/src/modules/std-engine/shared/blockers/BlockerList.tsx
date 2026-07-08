/**
 * UI-HARD-0120 — `<BlockerList />` (pack §6, doc §15.4).
 */

import type { ReactElement } from "react";

import { ResolutionActionLink } from "./ResolutionActionLink";
import type { StdEngineBlockerItem } from "./blocker.types";
import { safeUserPrimaryMessage, sanitizeDomToken } from "../safeUserMessage";

export type BlockerListProps = {
	blockers: StdEngineBlockerItem[];
	/** Shown when `blockers` is empty (still renders the list landmark). */
	emptyHint?: string;
	/** Override root list `data-testid` when embedding multiple lists (e.g. UI-HARD-0300 release groups). */
	listDataTestId?: string;
};

function severityLabel(s: StdEngineBlockerItem["severity"]): string {
	if (s === "critical") {
		return "Critical";
	}
	if (s === "warning") {
		return "Warning";
	}
	return "Info";
}

function severityClass(s: StdEngineBlockerItem["severity"]): string {
	if (s === "critical") {
		return "label label-danger";
	}
	if (s === "warning") {
		return "label label-warning";
	}
	return "label label-default";
}

export function BlockerList(props: BlockerListProps): ReactElement {
	const { blockers, emptyHint = "No blockers.", listDataTestId = "blocker-list" } = props;

	return (
		<ul data-testid={listDataTestId} className="list-unstyled std-engine-blocker-list" style={{ marginBottom: 0 }}>
			{blockers.length === 0 ? (
				<li className="text-muted">{emptyHint}</li>
			) : (
				blockers.map((b) => {
					const itemId = `blocker-item-${sanitizeDomToken(b.code)}`;
					const sectionHref = b.affectedSectionHref?.trim();
					const resolutionHref = b.resolutionHref?.trim();
					const message = safeUserPrimaryMessage(b.message);
					const why = b.whyItMatters ? safeUserPrimaryMessage(b.whyItMatters) : undefined;
					const resolution = b.resolutionAction ? safeUserPrimaryMessage(b.resolutionAction) : undefined;

					return (
						<li key={b.code} data-testid={itemId} className="std-engine-blocker-item" style={{ marginBottom: "1rem" }}>
							<div style={{ display: "flex", alignItems: "flex-start", gap: "0.5rem", flexWrap: "wrap" }}>
								<span className={severityClass(b.severity)} title={severityLabel(b.severity)}>
									{severityLabel(b.severity)}
								</span>
								<strong>{message}</strong>
							</div>
							<div className="text-muted small" style={{ marginTop: "0.25rem" }}>
								<span className="std-engine-blocker-affected">Where: {safeUserPrimaryMessage(b.affectedArea)}</span>
							</div>
							{why ? (
								<p className="small" style={{ marginTop: "0.35rem", marginBottom: 0 }}>
									<strong>Why it matters:</strong> {why}
								</p>
							) : null}
							{resolution ? (
								<p className="small" style={{ marginTop: "0.35rem", marginBottom: 0 }}>
									<strong>Fix:</strong> {resolution}
								</p>
							) : null}
							<div className="std-engine-blocker-links" style={{ marginTop: "0.5rem", display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
								{sectionHref ? (
									<ResolutionActionLink code={`${b.code}-section`} href={sectionHref} label="Open affected area" />
								) : null}
								{resolutionHref ? <ResolutionActionLink code={`${b.code}-resolve`} href={resolutionHref} label="Resolution" /> : null}
							</div>
						</li>
					);
				})
			)}
		</ul>
	);
}
