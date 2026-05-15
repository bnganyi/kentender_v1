import type { ActionAwareButtonProps, ReadinessUiStatus } from "../../shared";

export type PublicationOutputStatusRow = {
	label: string;
	statusLine: string;
};

/** User-readable publication failure (pack acceptance — no raw stacks). */
export type PublicationLastError = {
	message: string;
	resolutionAction?: string;
};

export type PublicationConfirmationScreenProps = {
	tenderCode: string;
	approvalStatusLabel: string;
	/** When false, publish control stays disabled with `publishPrerequisitesBlockedHint`. */
	approvalReady: boolean;
	readinessStatus: ReadinessUiStatus;
	readinessNarrative: string;
	readinessReady: boolean;
	outputStatuses: PublicationOutputStatusRow[];
	evidencePackageStatus: string;
	publicationSnapshotReadiness: string;
	/** `approvalReady && readinessReady` expected from host; still runs SEC-0410 on the live button. */
	publishPrerequisitesMet: boolean;
	publishPrerequisitesBlockedHint?: string;
	publishAction: Omit<ActionAwareButtonProps, "buttonTestId">;
	/** Shown after a failed publish attempt (optional). */
	publicationLastError?: PublicationLastError | null;
};
