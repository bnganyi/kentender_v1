import type { ActionAwareButtonProps } from "../../shared";

export type EvidencePackageViewScreenProps = {
	tenderCode: string;
	packageAndTenderLineage: string[];
	stdTemplateProfileLines: string[];
	stdInstanceLines: string[];
	generatedOutputsLines: string[];
	snapshotsLines: string[];
	approvalDecisionsLines: string[];
	auditEventsLines: string[];
	downstreamConsumptionRefs: string[];
	exportAction: Omit<ActionAwareButtonProps, "buttonTestId">;
};
