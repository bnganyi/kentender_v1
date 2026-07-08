/**
 * UI-HARD-0500 — Works completion workspace shell (pack §10, doc §9).
 *
 * Preferred Desk route: `/desk/tenders/{tender_code}/configure-document/works`
 */

import type { ReactNode } from "react";

import type { StdEngineBlockerItem } from "../../shared";

import type { OutputImpactKind } from "../components/outputImpactPanel.types";

/** Doc §9.4 / pack §10 — sidebar stage keys (short labels in UI). */
export type WorksCompletionStageId =
	| "tds"
	| "evaluation"
	| "works_requirements"
	| "drawings"
	| "boq"
	| "scc"
	| "outputs"
	| "readiness";

export type WorksCompletionStageRow = {
	id: WorksCompletionStageId;
	/** Sidebar label (plain language; pack uses short names like TDS). */
	label: string;
};

export const WORKS_COMPLETION_SIDEBAR_STAGES: readonly WorksCompletionStageRow[] = [
	{ id: "tds", label: "TDS" },
	{ id: "evaluation", label: "Evaluation Options" },
	{ id: "works_requirements", label: "Works Requirements" },
	{ id: "drawings", label: "Drawings" },
	{ id: "boq", label: "BOQ" },
	{ id: "scc", label: "SCC" },
	{ id: "outputs", label: "Outputs" },
	{ id: "readiness", label: "Readiness" },
] as const;

export type WorksCompletionAvailabilityAction = {
	actionCode: string;
	objectType: string;
	objectCode: string;
	availabilityContext?: Record<string, unknown>;
	onAllowedClick: () => void;
};

export type WorksCompletionWorkspacePageProps = {
	/** Doc §9.3 — tender context. */
	tenderCode: string;
	tenderTitle: string;
	packageCode: string;
	procurementCategory: string;
	procurementMethod: string;
	selectedStdTemplate: string;
	instanceState: string;
	publicationState: string;
	blockers?: StdEngineBlockerItem[];
	/** Doc §9.6 / UI-HARD-0510 — affected generated outputs (plain labels + pack `data-testid`s). */
	outputImpactAffectedKinds?: OutputImpactKind[];
	/**
	 * Selected sidebar stage. Omit for uncontrolled mode (first stage = TDS).
	 * When set, also pass `onStageSelect` for controlled usage.
	 */
	selectedStageId?: WorksCompletionStageId;
	onStageSelect?: (id: WorksCompletionStageId) => void;
	/** Main completion area; host injects stage forms. */
	mainPanel?: ReactNode;
	saveAction: WorksCompletionAvailabilityAction;
	generateOutputsAction: WorksCompletionAvailabilityAction | null;
	runReadinessAction: WorksCompletionAvailabilityAction | null;
};
