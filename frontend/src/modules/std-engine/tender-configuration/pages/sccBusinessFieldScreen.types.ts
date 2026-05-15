/**
 * UI-HARD-0610 — SCC business field screen (pack §11 SCC, doc §10.2).
 */

/** Pack “Required Fields Minimum”. */
export type SccFieldKey =
	| "completion_period_days"
	| "defects_liability_period_days"
	| "performance_security_percent"
	| "retention_percent"
	| "liquidated_damages_percent_per_day"
	| "maximum_liquidated_damages_percent"
	| "advance_payment_allowed"
	| "payment_currency"
	| "insurance_required"
	| "minimum_insurance_cover";

export type SccSaveAvailabilityAction = {
	actionCode: string;
	objectType: string;
	objectCode: string;
	availabilityContext?: Record<string, unknown>;
	onAllowedClick: () => void;
};

export type SccBusinessFieldScreenProps = {
	instanceCode: string;
	values: Partial<Record<SccFieldKey, string>>;
	onChange: (key: SccFieldKey, value: string) => void;
	fieldErrors?: Partial<Record<SccFieldKey, string>>;
	saveAction: SccSaveAvailabilityAction;
};

export type SccGroupDef = {
	id: string;
	title: string;
	sectionTestId: string;
	fieldKeys: readonly SccFieldKey[];
};

/** Pack required group titles + selectors (extra groups use consistent `scc-group-*` ids). */
export const SCC_BUSINESS_GROUPS: readonly SccGroupDef[] = [
	{
		id: "completion",
		title: "Completion Period",
		sectionTestId: "scc-group-completion-period",
		fieldKeys: ["completion_period_days"],
	},
	{
		id: "defects",
		title: "Defects Liability",
		sectionTestId: "scc-group-defects-liability",
		fieldKeys: ["defects_liability_period_days"],
	},
	{
		id: "performance",
		title: "Performance Security",
		sectionTestId: "scc-group-performance-security",
		fieldKeys: ["performance_security_percent"],
	},
	{
		id: "retention",
		title: "Retention",
		sectionTestId: "scc-group-retention",
		fieldKeys: ["retention_percent"],
	},
	{
		id: "ld",
		title: "Liquidated Damages",
		sectionTestId: "scc-group-liquidated-damages",
		fieldKeys: ["liquidated_damages_percent_per_day", "maximum_liquidated_damages_percent"],
	},
	{
		id: "payment",
		title: "Payment",
		sectionTestId: "scc-group-payment",
		fieldKeys: ["advance_payment_allowed", "payment_currency"],
	},
	{
		id: "insurance",
		title: "Insurance",
		sectionTestId: "scc-group-insurance",
		fieldKeys: ["insurance_required", "minimum_insurance_cover"],
	},
	{
		id: "dispute",
		title: "Dispute Resolution",
		sectionTestId: "scc-group-dispute-resolution",
		fieldKeys: [],
	},
] as const;

/** Pack “Required Help Example” (completion period). */
export const SCC_COMPLETION_PERIOD_HELP =
	"Completion period is carried into the contract and cannot be changed after publication except through controlled addendum or reissue workflow.";

export const SCC_FIELD_LABELS: Record<SccFieldKey, string> = {
	completion_period_days: "Completion period (days)",
	defects_liability_period_days: "Defects liability period (days)",
	performance_security_percent: "Performance security (%)",
	retention_percent: "Retention (%)",
	liquidated_damages_percent_per_day: "Liquidated damages (% per day)",
	maximum_liquidated_damages_percent: "Maximum liquidated damages (%)",
	advance_payment_allowed: "Advance payment allowed",
	payment_currency: "Payment currency",
	insurance_required: "Insurance required",
	minimum_insurance_cover: "Minimum insurance cover",
};
