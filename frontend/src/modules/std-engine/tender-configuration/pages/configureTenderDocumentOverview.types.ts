/**
 * UI-HARD-0400 — Configure Tender Document overview (pack §9, doc §8).
 *
 * Preferred Desk route (host): `/desk/tenders/{tender_code}/configure-document`
 */

import type { ReadinessUiStatus } from "../../shared";

/** Doc §8.4 — stage status vocabulary for the overview list. */
export type TenderConfigStageStatus =
	| "Not Started"
	| "Incomplete"
	| "Needs Attention"
	| "Complete"
	| "Stale"
	| "Locked"
	| "Not Applicable";

export type TenderConfigStageRow = {
	key: string;
	label: string;
	status: TenderConfigStageStatus;
};

/** Doc §8.5 — output kinds; UI shows plain labels plus acronym in parentheses where applicable. */
export type TenderConfigOutputKind = "bundle" | "dsm" | "dom" | "dem" | "dcm";

export type TenderConfigOutputRow = {
	kind: TenderConfigOutputKind;
	/** User-facing status (e.g. Current, Stale, Missing). */
	statusLabel: string;
};

/** Pack §9 — required Works stage labels (full wording, not internal acronyms alone). */
export const TENDER_CONFIGURE_WORKS_STAGE_LABELS: readonly string[] = [
	"Tender Data Sheet",
	"Evaluation and Qualification Options",
	"Works Requirements",
	"Drawings",
	"Bills of Quantities",
	"Special Conditions of Contract",
	"Generated Outputs",
	"Readiness",
	"Approval / Publication",
] as const;

/** Doc §8.5 — display line (status shown separately). */
export const TENDER_CONFIG_OUTPUT_PLAIN_LABEL: Record<TenderConfigOutputKind, string> = {
	bundle: "Tender document bundle",
	dsm: "Submission Rules (DSM)",
	dom: "Opening Register (DOM)",
	dem: "Evaluation Rules (DEM)",
	dcm: "Contract Carry-Forward (DCM)",
};

export type TenderConfigOverviewNextAction = {
	actionCode: string;
	objectType: string;
	objectCode: string;
	label: string;
	availabilityContext?: Record<string, unknown>;
	onAllowedClick: () => void;
};

export type ConfigureTenderDocumentOverviewPageProps = {
	tenderCode: string;
	tenderTitle: string;
	packageCode: string;
	packageTitle: string;
	/** Optional extra rows (category, method, etc.) — plain copy only; no raw mapping payloads. */
	contextLines?: Array<{ label: string; value: string }>;
	selectedStdSummary: string;
	/** Completion progress 0–100. */
	completionPercent: number;
	/** When omitted, defaults to Works stage list (all "Not Started"). Pass explicit `[]` for an empty list. */
	stages?: TenderConfigStageRow[] | undefined;
	outputs: TenderConfigOutputRow[];
	readinessStatus: ReadinessUiStatus;
	/** Optional secondary line under readiness badge. */
	readinessDetail?: string;
	/** Primary next step; backend-driven via `ActionAwareButton`. When `null`, section shows guidance only. */
	nextAction: TenderConfigOverviewNextAction | null;
};

export function defaultWorksTenderConfigStages(
	status: TenderConfigStageStatus = "Not Started",
): TenderConfigStageRow[] {
	return TENDER_CONFIGURE_WORKS_STAGE_LABELS.map((label, index) => ({
		key: `works-stage-${index}`,
		label,
		status,
	}));
}
