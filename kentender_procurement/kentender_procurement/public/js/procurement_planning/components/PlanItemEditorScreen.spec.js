// PLN-CHG-001 v1.18 (PLN18-305) — PlanItemEditorScreen component tests.
// U09's own five sections (Requirement and sources, Package details, Method
// and eligibility, Reservation and structure, Baseline schedule), the
// CONFIG-missing notice, eligibility conditions + Declaration evidence, the
// read-only Reservation/structure facts (no highest-advantage ranking or
// override reason, no multi-year, no county checkbox — §17.4/spec line 1265)
// and the scope-lock/correction-hold notices (U09-locked).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PlanItemEditorScreen from "./PlanItemEditorScreen.vue";

const SINGLE = {
	outcome: "OK",
	plan_item_id: "PPI-MOH-2027-021",
	record_version: 0,
	mutable: true,
	can_act: true,
	combined: false,
	is_active: false,
	source_correction_required: false,
	header: {
		eyebrow: "PLAN ITEM",
		title: "National digital health infrastructure upgrade",
		reference_line: "PPI-MOH-2027-021 · Draft Version 1",
		item_state_badge: "Proposed",
	},
	plan_reference: "PLN-MOH-2027-001",
	sources: [
		{
			requirement: "National digital health infrastructure upgrade", department: "Digital Health",
			source_origin: "Accepted Departmental Need",
			need_reference_line: "NDS-MOH-2027-0001 · Revision 1",
			quantity_display: "1 programme", quantity_number: "1", unit_label: "Programme",
			required_by_display: "31 Aug 2027",
			budget_line: "BL-1", budget_line_display: "MOH-BL-DHI-2027 — Digital health infrastructure programme",
			amount_display: "KES 80,000,000",
		},
	],
	sources_caption: "",
	planned_value_display: "KES 80,000,000",
	total_quantity_display: "1 programme",
	notices: [],
	identity: {
		title: "National digital health infrastructure upgrade",
		description: "Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme.",
		requirement_type: "Non-consulting services",
		procurement_category: "Services",
		aggregation_reason: "",
	},
	scope_lock: { locked: false, since: "", first_requisition: "", held: false, open_requests: 0 },
	classification: {
		strategic_objective: "OBJ-1",
		objective_path: "Digital health systems › Health policy, standards and regulation › Digital health governance",
		objective_eligible: true,
		strategic_objectives: [
			{ id: "OBJ-1", reference: "OBJ-MOH-2023-001", title: "Strengthen interoperable national digital health services", path_display: "Digital health systems › Health policy, standards and regulation › Digital health governance" },
		],
		procurement_method: "Open Tender",
		admissible_methods: ["Open Tender", "Restricted Tender", "Request for Proposals"],
		proposed_method: "Open Tender",
		reference_available: true,
		method_profile: {
			found: true, profile: "MPR-OPEN-TENDER-V2", version_number: 2,
			conditions: [
				{ condition_id: "G-VALUE", kind: "Known fact", description: "Value within the funds allocated.", mandatory: true, result: "Met" },
			],
			evidence_complete: true, missing_evidence: [],
		},
		method_condition_evidence: [],
		estimate_basis: "Based on the 2027 market survey of comparable digital-health infrastructure programmes.",
		estimate_basis_reference: "MPR-2027-014",
	},
	preference: {
		reservation_category: "None",
		reservation_categories: ["None", "Youth", "Women", "Persons with disability", "Micro, small and medium enterprise"],
		county_resident_reservation: false,
		county_control_available: false,
		plan_horizon: "Single year",
		aggregation_indicator: "Not aggregated",
		lotting_indicator: "Single lot",
		lot_count: 0,
		mandatory_restrictions_line: "No additional restriction applies",
		helper: "The planned designation from the governed catalogue. Choose None where no designation applies; candidate entitlement is assessed downstream.",
	},
	baseline: {
		target_invitation_date: "2027-05-01",
		periods: { tendering_period_days: 21, evaluation_period_days: 30, award_approval_buffer_days: 5, notification_buffer_days: 2, standstill_period_days: 14 },
		defaults: { tendering_period_days: 21, evaluation_period_days: 30, award_approval_buffer_days: 5, notification_buffer_days: 2, standstill_period_days: 14 },
		using_defaults: true,
		defaults_line: "Using governed defaults for Services · Open Tender",
		floors: { tendering_period_days: 7, standstill_period_days: 14 },
		ceilings: { evaluation_period_days: 30 },
		estimated_delivery_period_days: 60,
		estimated_completion_display: "31 Aug 2027",
		rows: [
			{ milestone: "invitation", label: "Invitation or advertisement", date: "2027-05-01", date_display: "1 May 2027" },
			{ milestone: "bid_opening", label: "Bid opening", date: "2027-05-22", date_display: "22 May 2027" },
			{ milestone: "evaluation_completion", label: "Evaluation completion", date: "2027-06-21", date_display: "21 Jun 2027" },
			{ milestone: "award_approval", label: "Tender award approval", date: "2027-06-26", date_display: "26 Jun 2027" },
			{ milestone: "award_notification", label: "Notification of award", date: "2027-06-28", date_display: "28 Jun 2027" },
			{ milestone: "contract_signing", label: "Contract signing", date: "2027-07-12", date_display: "12 Jul 2027" },
			{ milestone: "delivery_completion", label: "Delivery or implementation completion", date: "2027-08-31", date_display: "31 Aug 2027", from_requisition: true },
		],
		delivery_boundary_ok: true,
		locked: false,
	},
	schedule: [],
	revisions: [],
	market_price_index: { published: false, rows: [], helper: "Market price index: not published for this category." },
	blockers: [],
};

const COMBINED = {
	...SINGLE,
	combined: true,
	header: { ...SINGLE.header, title: "Clinical training and deployment laptops for digital health rollout", reference_line: "PPI-MOH-2027-033 · Draft Version 1" },
	sources: [
		{ ...SINGLE.sources[0], requirement: "Clinical training laptops for digital health rollout", department: "Human Resources Management and Development", quantity_display: "200 each", quantity_number: "200", unit_label: "Each", required_by_display: "31 Dec 2027", budget_line_display: "MOH-BL-HWD-2027 — Health workforce programme", amount_display: "KES 48,000,000" },
		{ ...SINGLE.sources[0], requirement: "Clinical deployment laptops for digital health rollout", quantity_display: "300 each", quantity_number: "300", unit_label: "Each", required_by_display: "31 Dec 2027", amount_display: "KES 72,000,000" },
	],
	sources_caption: "2 sources · 500 each · KES 120,000,000",
	total_quantity_display: "500 each",
	identity: { ...SINGLE.identity, requirement_type: "Goods", procurement_category: "Goods", aggregation_reason: "Procure one standard laptop specification and deployment service for the same national digital-health rollout." },
};

const CONFIG_MISSING = {
	...SINGLE,
	classification: { ...SINGLE.classification, reference_available: false, method_profile: { found: false, conditions: [], evidence_complete: true, missing_evidence: [] } },
};

const DECLARATION_METHOD = {
	...SINGLE,
	classification: {
		...SINGLE.classification,
		procurement_method: "Direct Procurement",
		method_profile: {
			found: true, profile: "MPR-DIRECT-V1", version_number: 1,
			conditions: [
				{ condition_id: "CIRCUMSTANCES", kind: "Declaration", description: "Circumstances supporting the selected method.", mandatory: true, result: "Evidence required", required_evidence: "Method eligibility record", authorisation_actor: "Head of Procurement Function", evidence_reference: "", authorisation_reference: "" },
			],
			evidence_complete: false, missing_evidence: ["CIRCUMSTANCES"],
		},
		method_condition_evidence: [],
	},
};

const LOCKED = {
	...SINGLE,
	mutable: false,
	is_active: true,
	header: { ...SINGLE.header, item_state_badge: "Active" },
	scope_lock: { locked: true, since: "2027-03-15 09:00:00", first_requisition: "REQ-MOH-2027-033-001", held: false, open_requests: 0 },
	notices: [
		{ kind: "scope_locked", heading: "Additional requirements need a separate Plan Item", text: "This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement." },
	],
};

function make(item = SINGLE) {
	return mount(PlanItemEditorScreen, { props: { item, pending: false, errorSummary: "" } });
}

describe("PlanItemEditorScreen — U09 single source", () => {
	it("renders the Requirement and sources table with Source/Department/Quantity/Unit/Amount", () => {
		const w = make();
		const card = w.find('[data-testid="ppi-sources"]');
		expect(card.find(".kt-card-title").text()).toBe("Requirement and sources");
		expect(card.findAll("thead th").map((th) => th.text())).toEqual([
			"Source", "Department", "Quantity", "Unit", "Required by", "Procurement Budget Line", "Amount",
		]);
		const cells = card.findAll("tbody tr")[0].findAll("td").map((td) => td.text());
		expect(cells).toEqual([
			"NDS-MOH-2027-0001 · Revision 1", "Digital Health", "1", "Programme", "31 Aug 2027",
			"MOH-BL-DHI-2027 — Digital health infrastructure programme", "KES 80,000,000",
		]);
		expect(w.find('[data-testid="ppi-price-index"]').text()).toBe("Market price index: not published for this category.");
		expect(w.find('[data-testid="ppi-badge"]').text()).toBe("Proposed");
	});

	it("renders Package details with title/description/objective/estimate basis and the Quantity+Value facts, no aggregation reason", () => {
		const w = make();
		const card = w.find('[data-testid="ppi-package"]');
		expect(card.find('[data-testid="ppi-title"]').element.value).toBe("National digital health infrastructure upgrade");
		expect(card.find('[data-testid="ppi-aggregation"]').exists()).toBe(false);
		expect(card.find('[data-testid="ppi-estimate-basis"]').element.value).toContain("2027 market survey");
		expect(card.find('[data-testid="ppi-estimate-basis-reference"]').element.value).toBe("MPR-2027-014");
		expect(card.text()).toContain("Digital health systems › Health policy");
		const facts = card.findAll(".pln-fact");
		expect(facts.map((f) => f.get(".kt-label").text())).toEqual(["Quantity", "Value"]);
		expect(facts.map((f) => f.get(".pln-fact-val").text())).toEqual(["1 programme", "KES 80,000,000"]);
	});

	it("shows the CONFIG-missing notice instead of the eligibility content when no profile is in force", () => {
		const w = make(CONFIG_MISSING);
		const card = w.find('[data-testid="ppi-method-config-missing"]');
		expect(card.text()).toContain("Procurement rules are not configured");
		expect(card.text()).toContain("Draft work can continue where permitted; the affected submission is unavailable.");
		expect(w.find('select[data-testid="ppi-method"]').exists()).toBe(false);
	});

	it("renders Method and eligibility with the admissible-method select, Procedure profile fact and the conditions table", () => {
		const w = make();
		const card = w.find('[data-testid="ppi-method-card"]');
		const select = w.find('select[data-testid="ppi-method"]');
		expect(select.findAll("option").map((o) => o.text())).toEqual(["Open Tender", "Restricted Tender", "Request for Proposals"]);
		expect(select.element.value).toBe("Open Tender");
		expect(card.text()).toContain("MPR-OPEN-TENDER-V2, Version 2");
		expect(card.text()).toContain("Conditions");
		expect(card.text()).toContain("Complete");
		const rows = card.findAll('[data-testid="ppi-conditions"] tbody tr');
		expect(rows).toHaveLength(1);
		expect(rows[0].findAll("td")[0].text()).toBe("Value within the funds allocated.");
		expect(rows[0].text()).toContain("Met");
	});

	it("renders a Declaration condition's evidence input and the required-authorisation fact only for that condition", () => {
		const w = make(DECLARATION_METHOD);
		const input = w.find('[data-testid="ppi-evidence-CIRCUMSTANCES"]');
		expect(input.exists()).toBe(true);
		const label = w.findAll("label").find((l) => l.attributes("for") === "ppi-evidence-CIRCUMSTANCES");
		expect(label.text()).toBe("Circumstances supporting the selected method");
		expect(w.text()).toContain("Required specific authorisation");
		expect(w.text()).toContain("Head of Procurement Function");
		expect(w.find('[data-testid="ppi-authorisation-CIRCUMSTANCES"]').exists()).toBe(true);
	});

	it("does not offer an evidence input for a Known-fact-only method (§12.8: no universal checkbox)", () => {
		const w = make();
		expect(w.find('[data-testid^="ppi-evidence-"]').exists()).toBe(false);
	});

	it("renders Reservation and structure as read-only facts with only Planned reservation and Lot count editable, no ranking/override/multi-year/county control", () => {
		const w = make();
		const card = w.find('[data-testid="ppi-preference"]');
		expect(w.find('select[data-testid="ppi-reservation"]').exists()).toBe(true);
		expect(card.text()).toContain("No additional restriction applies");
		expect(card.text()).toContain("Single year");
		expect(card.text()).toContain("Not aggregated");
		expect(card.text()).toContain("Single lot");
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-horizon"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-aggregation-indicator"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-lotting"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-multi-year"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-reservation-reason"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-county"]').exists()).toBe(false);
	});

	it("shows an editable Lot count and the 'Structure — Packaged into lots' title once already packaged", () => {
		const w = make({ ...SINGLE, preference: { ...SINGLE.preference, lotting_indicator: "Packaged into lots", lot_count: 2 } });
		const input = w.find('[data-testid="ppi-lot-count"]');
		expect(input.exists()).toBe(true);
		expect(input.element.value).toBe("2");
		expect(w.find('[data-testid="ppi-preference"] .kt-card-title').text()).toBe("Structure — Packaged into lots");
	});

	it("computes the seven baseline dates from the target date and periods, live, before any save (PLN-AC-115)", async () => {
		const w = make();
		const card = w.find('[data-testid="ppi-baseline"]');
		expect(card.find('[data-testid="ppi-target-date"]').element.value).toBe("2027-05-01");
		const dates = () => card.findAll('[data-testid="ppi-baseline-table"] tbody tr').map((r) => r.findAll("td")[1].text());
		expect(dates()).toEqual([
			"1 May 2027", "22 May 2027", "21 Jun 2027", "26 Jun 2027", "28 Jun 2027", "12 Jul 2027",
			"31 Aug 2027 · from the authorised Requisition",
		]);
		expect(w.find('[data-testid="ppi-periods-summary"]').text()).toBe("Using governed defaults for Services · Open Tender");
		expect(w.find('[data-testid="ppi-periods"]').exists()).toBe(false);
		await card.find('[data-testid="ppi-target-date"]').setValue("2027-05-15");
		expect(dates()[1]).toBe("5 Jun 2027");
		await w.find('[data-testid="ppi-adjust-periods"]').trigger("click");
		expect(w.find('[data-testid="ppi-periods"]').findAll("label").map((l) => l.text())).toEqual([
			"Tendering", "Evaluation", "Award approval buffer", "Notification buffer", "Standstill",
		]);
		await w.find('[data-testid="ppi-tendering_period_days"]').setValue("7");
		expect(dates()[1]).toBe("22 May 2027");
		expect(w.find('[data-testid="ppi-boundary-warning"]').exists()).toBe(false);
	});

	it("warns when the computed signing date leaves no delivery period (invariant 12a)", async () => {
		const w = make();
		await w.find('[data-testid="ppi-target-date"]').setValue("2027-08-20");
		expect(w.find('[data-testid="ppi-boundary-warning"]').exists()).toBe(true);
	});

	it("emits save with exactly the §12.8 inputs — never a milestone date, never the removed fields", async () => {
		const w = make();
		await w.find('[data-testid="ppi-title"]').setValue("Renamed package");
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const [payload] = w.emitted("save")[0];
		expect(payload.title).toBe("Renamed package");
		expect(payload.strategic_objective).toBe("OBJ-1");
		expect(payload.procurement_method).toBe("Open Tender");
		expect(payload.estimate_basis).toContain("2027 market survey");
		expect(payload.estimate_basis_reference).toBe("MPR-2027-014");
		expect(payload.baseline_invitation_date).toBe("2027-05-01");
		expect(payload.tendering_period_days).toBe(21);
		expect(payload.standstill_period_days).toBe(14);
		expect(Object.keys(payload).some((k) => /_date$/.test(k) && k !== "baseline_invitation_date")).toBe(false);
		expect(payload).not.toHaveProperty("aggregation_reason");
		expect(payload).not.toHaveProperty("plan_horizon");
		expect(payload).not.toHaveProperty("aggregation_indicator");
		expect(payload).not.toHaveProperty("lotting_indicator");
		expect(payload).not.toHaveProperty("multi_year_justification");
		expect(payload).not.toHaveProperty("reservation_category_reason");
		expect(payload).not.toHaveProperty("county_resident_reservation");
	});

	it("includes method_condition_evidence only when a Declaration condition has been given evidence", async () => {
		const w = make(DECLARATION_METHOD);
		await w.find('[data-testid="ppi-evidence-CIRCUMSTANCES"]').setValue("MER-PLNT-001");
		await w.find('[data-testid="ppi-authorisation-CIRCUMSTANCES"]').setValue("AO/2101/DP/1");
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const [payload] = w.emitted("save")[0];
		expect(payload.method_condition_evidence).toEqual([
			{ condition_id: "CIRCUMSTANCES", evidence_reference: "MER-PLNT-001", authorisation_reference: "AO/2101/DP/1" },
		]);
	});

	it("marks the control a readiness blocker names (PLN-AC-114)", () => {
		const w = make({ ...SINGLE, blockers: [{ code: "PLN_STANDSTILL_BELOW_MINIMUM", field: "standstill_period_days" }, { code: "PLN_OBJECTIVE_INELIGIBLE", field: "strategic_objective" }] });
		expect(w.find('[data-testid="ppi-objective"]').attributes("aria-invalid")).toBe("true");
		expect(w.find('select[data-testid="ppi-method"]').attributes("aria-invalid")).toBeUndefined();
	});

	it("carries Back, Dissolve and Save draft and no Finance, forecast or actual control (§11.10)", () => {
		const w = make();
		const footer = w.find(".pln-footer-bar");
		expect(footer.findAll("button").map((b) => b.text())).toEqual(["Back to Annual Plan", "Dissolve Plan Item", "Save draft"]);
		expect(w.text()).not.toContain("Finance");
		expect(w.text()).not.toContain("Forecast");
		expect(w.text()).not.toContain("Actual");
	});

	it("shows the source-correction notice while Save and Dissolve remain visible (§12.7)", () => {
		const w = make({ ...SINGLE, source_correction_required: true });
		expect(w.find('[data-testid="ppi-source-correction"]').text()).toContain("Source correction required");
		expect(w.find('[data-testid="ppi-save"]').exists()).toBe(true);
		expect(w.find('[data-testid="ppi-dissolve"]').exists()).toBe(true);
	});

	it("a non-mutable item offers no editing affordances", () => {
		const w = make({ ...SINGLE, mutable: false });
		expect(w.find('[data-testid="ppi-save"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-dissolve"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-title"]').attributes("disabled")).toBeDefined();
	});
});

describe("PlanItemEditorScreen — U09 combined", () => {
	it("renders two source rows, the caption, the aggregation reason and the summed Quantity fact", () => {
		const w = make(COMBINED);
		const sources = w.find('[data-testid="ppi-sources"]');
		expect(sources.findAll("tbody tr")).toHaveLength(2);
		expect(sources.text()).toContain("2 sources · 500 each · KES 120,000,000");
		const pkg = w.find('[data-testid="ppi-package"]');
		expect(pkg.find('[data-testid="ppi-aggregation"]').element.value).toContain("Procure one standard laptop specification");
		const facts = pkg.findAll(".pln-fact");
		expect(facts.find((f) => f.get(".kt-label").text() === "Quantity").get(".pln-fact-val").text()).toBe("500 each");
	});

	it("emits save including the aggregation reason", async () => {
		const w = make(COMBINED);
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const [payload] = w.emitted("save")[0];
		expect(payload.aggregation_reason).toContain("Procure one standard laptop specification");
	});
});

describe("PlanItemEditorScreen — U09-locked", () => {
	it("shows the Active badge, the scope-locked notice with Requisition/Date and Original allowance heading, no Save or Dissolve", () => {
		const w = make(LOCKED);
		expect(w.find('[data-testid="ppi-badge"]').text()).toBe("Active");
		const notice = w.find('[data-testid="ppi-notice-scope_locked"]');
		expect(notice.text()).toContain("This Plan Item already has an authorised Requisition");
		expect(notice.text()).toContain("REQ-MOH-2027-033-001");
		const sources = w.find('[data-testid="ppi-sources"]');
		expect(sources.findAll("thead th").map((th) => th.text())).toContain("Original allowance");
		expect(w.find('[data-testid="ppi-save"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-dissolve"]').exists()).toBe(false);
	});
});
