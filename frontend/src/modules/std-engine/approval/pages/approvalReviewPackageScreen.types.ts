import type { ActionAwareButtonProps, ReadinessUiStatus, StdEngineBlockerItem } from "../../shared";

/** Doc §16.4 — POST …/approval/return body fields (names match pack). */
export type ApprovalReturnForCorrectionPayload = {
	reason_code: string;
	comment: string;
	affected_area: string;
	criticality: string;
};

export type ApprovalReviewSelectOption = { value: string; label: string };

export type ApprovalReviewPackageScreenProps = {
	tenderCode: string;
	/** Route context (pack §16). */
	tenderSummaryLines: string[];
	packageReferenceLines: string[];
	stdTemplateProfileSummary: string[];
	readinessStatus: ReadinessUiStatus;
	readinessNarrative: string;
	/** Read-only bundle preview (host supplies escaped/plain text). */
	bundlePreviewText: string;
	outputSummaryLines: string[];
	boqSummaryLines: string[];
	worksRequirementsSummaryLines: string[];
	warningsBlockers: StdEngineBlockerItem[];
	auditEvidenceSummaryLines: string[];
	decisionHistoryLines: string[];
	approveAction: Omit<ActionAwareButtonProps, "buttonTestId">;
	returnAction: Omit<ActionAwareButtonProps, "buttonTestId" | "onAllowedClick"> & {
		onReturnConfirmed: (payload: ApprovalReturnForCorrectionPayload) => void;
	};
	/** Doc §16.3 — optional when workflow registers these actions. */
	rejectAction?: Omit<ActionAwareButtonProps, "buttonTestId"> | null;
	requestClarificationAction?: Omit<ActionAwareButtonProps, "buttonTestId"> | null;
	reasonCodeOptions: ApprovalReviewSelectOption[];
	criticalityOptions: ApprovalReviewSelectOption[];
};
