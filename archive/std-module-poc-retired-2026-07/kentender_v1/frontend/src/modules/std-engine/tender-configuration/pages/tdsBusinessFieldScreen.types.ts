/**
 * UI-HARD-0600 — TDS business field screen (pack §11 TDS, doc §10.1).
 *
 * API (host): `PUT /api/std-engine/works/instances/{instance_code}/tds-values`
 */

/** SEC-0410 payload for the save control (same shape as other std-engine screens). */
export type TdsSaveAvailabilityAction = {
	actionCode: string;
	objectType: string;
	objectCode: string;
	availabilityContext?: Record<string, unknown>;
	onAllowedClick: () => void;
};

/** Pack “Required Fields Minimum” (structured keys; values are strings for form state). */
export type TdsFieldKey =
	| "tender_title"
	| "procuring_entity_name"
	| "project_location"
	| "submission_deadline"
	| "opening_datetime"
	| "clarification_deadline"
	| "bid_validity_days"
	| "tender_security_required"
	| "tender_security_type"
	| "tender_security_amount"
	| "tender_security_currency"
	| "site_visit_required"
	| "site_visit_datetime"
	| "site_visit_location"
	| "pre_tender_meeting_required"
	| "bid_currency"
	| "language";

export type TdsBusinessFieldScreenProps = {
	/** Works STD instance (SEC-0410 object code for save). */
	instanceCode: string;
	values: Partial<Record<TdsFieldKey, string>>;
	onChange: (key: TdsFieldKey, value: string) => void;
	fieldErrors?: Partial<Record<TdsFieldKey, string>>;
	/** Save must be backend availability–driven (pack). */
	saveAction: TdsSaveAvailabilityAction;
};

export type TdsGroupDef = {
	id: string;
	title: string;
	sectionTestId: string;
	fieldKeys: readonly TdsFieldKey[];
};

/** Pack required groups + doc §10.1 ordering. */
export const TDS_BUSINESS_GROUPS: readonly TdsGroupDef[] = [
	{
		id: "identity",
		title: "Tender Identity",
		sectionTestId: "tds-group-tender-identity",
		fieldKeys: ["tender_title", "procuring_entity_name", "project_location"],
	},
	{
		id: "dates",
		title: "Dates and Deadlines",
		sectionTestId: "tds-group-dates",
		fieldKeys: ["submission_deadline", "opening_datetime", "clarification_deadline"],
	},
	{
		id: "security",
		title: "Tender Security",
		sectionTestId: "tds-group-security",
		fieldKeys: ["tender_security_required", "tender_security_type", "tender_security_amount", "tender_security_currency"],
	},
	{
		id: "site",
		title: "Site Visit / Pre-Tender Meeting",
		sectionTestId: "tds-group-site-visit",
		fieldKeys: ["site_visit_required", "site_visit_datetime", "site_visit_location", "pre_tender_meeting_required"],
	},
	{
		id: "bid",
		title: "Bid Validity",
		sectionTestId: "tds-group-bid-validity",
		fieldKeys: ["bid_validity_days"],
	},
	{
		id: "submission",
		title: "Submission Instructions",
		sectionTestId: "tds-group-submission-instructions",
		fieldKeys: [],
	},
	{
		id: "lang",
		title: "Language and Currency",
		sectionTestId: "tds-group-language-currency",
		fieldKeys: ["bid_currency", "language"],
	},
	{
		id: "complaints",
		title: "Complaints / Review",
		sectionTestId: "tds-group-complaints-review",
		fieldKeys: [],
	},
] as const;

export const TDS_FIELD_LABELS: Record<TdsFieldKey, string> = {
	tender_title: "Tender title",
	procuring_entity_name: "Procuring entity name",
	project_location: "Project location",
	submission_deadline: "Submission deadline",
	opening_datetime: "Opening date and time",
	clarification_deadline: "Clarification deadline",
	bid_validity_days: "Bid validity (days)",
	tender_security_required: "Tender security required",
	tender_security_type: "Tender security type",
	tender_security_amount: "Tender security amount",
	tender_security_currency: "Tender security currency",
	site_visit_required: "Site visit required",
	site_visit_datetime: "Site visit date and time",
	site_visit_location: "Site visit location",
	pre_tender_meeting_required: "Pre-tender meeting required",
	bid_currency: "Bid currency",
	language: "Language",
};
