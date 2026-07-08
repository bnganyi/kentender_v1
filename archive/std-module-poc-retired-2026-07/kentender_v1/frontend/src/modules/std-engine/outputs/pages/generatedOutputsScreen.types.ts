/**
 * UI-HARD-0900 — Generated outputs (pack §14, doc §14).
 */

export type GeneratedOutputKind = "bundle" | "dsm" | "dom" | "dem" | "dcm";

export const GENERATED_OUTPUT_KIND_ORDER: readonly GeneratedOutputKind[] = ["bundle", "dsm", "dom", "dem", "dcm"] as const;

/** Plain labels (pack “Required Output Cards”). */
export const GENERATED_OUTPUT_CARD_TITLE: Record<GeneratedOutputKind, string> = {
	bundle: "Tender Document Bundle",
	dsm: "Submission Rules (DSM)",
	dom: "Opening Register (DOM)",
	dem: "Evaluation Rules (DEM)",
	dcm: "Contract Carry-Forward (DCM)",
};

export type GeneratedOutputCardState = {
	status: string;
	version: string;
	generatedAt: string;
	stale: boolean;
	sourceSnapshot?: string | null;
};

export type GenerateAllAvailabilityAction = {
	actionCode: string;
	objectType: string;
	objectCode: string;
	availabilityContext?: Record<string, unknown>;
	onAllowedClick: () => void;
};

export type GeneratedOutputsScreenProps = {
	/** Shown in header (e.g. tender or instance context). */
	contextTitle: string;
	outputs: Partial<Record<GeneratedOutputKind, GeneratedOutputCardState>>;
	generateAllAction: GenerateAllAvailabilityAction;
	onPreview?: (kind: GeneratedOutputKind) => void;
	onDownload?: (kind: GeneratedOutputKind) => void;
	onViewSummary?: (kind: GeneratedOutputKind) => void;
	/** When false, traceability control is hidden (permission gate). */
	traceabilityAllowed?: boolean;
	onViewTraceability?: (kind: GeneratedOutputKind) => void;
};
