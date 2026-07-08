/**
 * UI-HARD-0700 — Works requirements component cards (pack §12, doc §11).
 */

export type WorksRequirementComponentId =
	| "specifications"
	| "site_information"
	| "hse"
	| "environmental_social"
	| "method_statement"
	| "work_programme"
	| "quality";

export type WorksRequirementStatus = "Not Started" | "Incomplete" | "Complete" | "Needs Attention";

export type AttachmentClassification = "supplier_facing" | "internal_only" | "contract_facing";

export type WorksRequirementCardDef = {
	id: WorksRequirementComponentId;
	title: string;
	/** Pack `data-testid` (pack lists a subset; remaining cards use consistent `works-component-*` ids). */
	sectionTestId: string;
};

/** Doc §11.1 titles; `sectionTestId` matches pack §12 required selectors where provided. */
export const WORKS_REQUIREMENT_CARD_DEFS: readonly WorksRequirementCardDef[] = [
	{ id: "specifications", title: "Specifications", sectionTestId: "works-component-specifications" },
	{ id: "site_information", title: "Site Information", sectionTestId: "works-component-site-information" },
	{ id: "hse", title: "HSE Requirements", sectionTestId: "works-component-hse" },
	{
		id: "environmental_social",
		title: "Environmental / Social Requirements",
		sectionTestId: "works-component-environmental-social",
	},
	{ id: "method_statement", title: "Method Statement Requirement", sectionTestId: "works-component-method-statement" },
	{ id: "work_programme", title: "Work Programme Requirement", sectionTestId: "works-component-work-programme" },
	{ id: "quality", title: "Quality Requirements", sectionTestId: "works-component-quality" },
] as const;

export type WorksRequirementsScreenProps = {
	/** Per-component readiness-style status (acceptance: component status visible). */
	componentStatuses?: Partial<Record<WorksRequirementComponentId, WorksRequirementStatus>>;
	/** Optional host notice when attachments are still unbound / readiness blocked. */
	readinessNotice?: string | null;
	/** Called when user picks a file after all bindings are set (host performs upload). */
	onAttachmentFileChosen?: (args: {
		componentId: WorksRequirementComponentId;
		sectionCode: string;
		classification: AttachmentClassification;
		file: File;
	}) => void;
};
