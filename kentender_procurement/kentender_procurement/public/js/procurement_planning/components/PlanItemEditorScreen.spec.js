// PLN-CHG-001 v1.12 §15 — PlanItemEditorScreen component tests (D14).
// PLN-DES-09 (single source) and PLN-DES-09A (combined): exact cards, the
// admissible-method select, the conditional preference fields, and the
// baseline schedule that recomputes live before any save (PLN-AC-115).
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
			departmental_plan_line: "DPP-MOH-DHI-2027-001 · Version 1",
			need_reference_line: "NDS-MOH-2027-0001 · Version 1",
			quantity_display: "1 programme", required_by_display: "31 Aug 2027",
			budget_line: "BL-1", budget_line_display: "MOH-BL-DHI-2027 — Digital health infrastructure programme",
			amount_display: "KES 80,000,000",
		},
	],
	sources_caption: "",
	planned_value_display: "KES 80,000,000",
	identity: {
		title: "National digital health infrastructure upgrade",
		description: "Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme.",
		requirement_type: "Non-consulting services",
		procurement_category: "Services",
		aggregation_reason: "",
	},
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
		value_band: "Above KES 5,000,000 · Open Tender admissible",
		reference_available: true,
	},
	preference: {
		reservation_category: "None",
		reservation_category_reason: "",
		reservation_categories: ["None", "Youth", "Women", "Persons with disability", "Micro, small and medium enterprise"],
		highest_advantage: "Youth",
		county_resident_reservation: false,
		county_control_available: false,
		exclusive_preference: false,
		plan_horizon: "Single year",
		multi_year_justification: "",
		aggregation_indicator: "Not aggregated",
		lotting_indicator: "Single lot",
		lot_count: 0,
		helper: "Recorded for the entity's 30% target. Choose None only where no reservation applies.",
	},
	baseline: {
		target_invitation_date: "2027-05-01",
		periods: { tendering_period_days: 21, evaluation_period_days: 30, award_approval_buffer_days: 5, notification_buffer_days: 2, standstill_period_days: 14 },
		defaults: { tendering_period_days: 21, evaluation_period_days: 30, award_approval_buffer_days: 5, notification_buffer_days: 2, standstill_period_days: 14 },
		using_defaults: true,
		defaults_line: "Using governed defaults for Services · Open Tender",
		floors: { tendering_period_days: 7, standstill_period_days: 14 },
		ceilings: { evaluation_period_days: 30 },
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
		{ ...SINGLE.sources[0], requirement: "Clinical training laptops for digital health rollout", department: "Human Resources Management and Development", quantity_display: "200 each", required_by_display: "31 Dec 2027", budget_line_display: "MOH-BL-HWD-2027 — Health workforce programme", amount_display: "KES 48,000,000" },
		{ ...SINGLE.sources[0], requirement: "Clinical deployment laptops for digital health rollout", quantity_display: "300 each", required_by_display: "31 Dec 2027", amount_display: "KES 72,000,000" },
	],
	sources_caption: "2 sources · 500 each · KES 120,000,000",
	identity: { ...SINGLE.identity, requirement_type: "Goods", procurement_category: "Goods", aggregation_reason: "Procure one standard laptop specification and deployment service for the same national digital-health rollout." },
	preference: { ...SINGLE.preference, aggregation_indicator: "Aggregated into this package" },
};

function make(item = SINGLE) {
	return mount(PlanItemEditorScreen, { props: { item, pending: false, errorSummary: "" } });
}

describe("PlanItemEditorScreen — PLN-DES-09 single source", () => {
	it("renders the eight read-only source rows, the price-index helper and no source table", () => {
		const w = make();
		const source = w.find('[data-testid="ppi-source"]');
		expect(source.find(".kt-card-title").text()).toBe("Departmental source");
		expect(source.findAll("label").map((l) => l.text())).toEqual([
			"Department", "Source origin", "Departmental plan", "Accepted Need", "Quantity", "Required by", "Procurement Budget Line", "Planned value",
		]);
		expect(source.text()).toContain("MOH-BL-DHI-2027 — Digital health infrastructure programme");
		expect(source.findAll("input, textarea, select")).toHaveLength(0);
		expect(w.find('[data-testid="ppi-price-index"]').text()).toBe("Market price index: not published for this category.");
		expect(w.find('[data-testid="ppi-sources"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-badge"]').text()).toBe("Proposed");
	});

	it("renders Identity with editable title/description and read-only requirement type, no aggregation reason", () => {
		const w = make();
		const card = w.find('[data-testid="ppi-identity"]');
		expect(card.find('[data-testid="ppi-title"]').element.value).toBe("National digital health infrastructure upgrade");
		expect(card.text()).toContain("Non-consulting services");
		expect(card.find('[data-testid="ppi-aggregation"]').exists()).toBe(false);
	});

	it("offers Strategic Objective and only the admissible methods as selects, path and band read-only", () => {
		const w = make();
		const card = w.find('[data-testid="ppi-classification"]');
		expect(card.findAll("label").map((l) => l.text())).toEqual(["Strategic Objective", "Objective path", "Procurement method", "Value band"]);
		const objective = card.find('[data-testid="ppi-objective"]');
		expect(objective.find("option[value='OBJ-1']").text()).toBe("OBJ-MOH-2023-001 — Strengthen interoperable national digital health services");
		expect(card.text()).toContain("Digital health systems › Health policy");
		const method = card.find('[data-testid="ppi-method"]');
		expect(method.findAll("option").map((o) => o.text())).toEqual(["Open Tender", "Restricted Tender", "Request for Proposals"]);
		expect(method.element.value).toBe("Open Tender");
		expect(w.find('[data-testid="ppi-value-band"]').text()).toBe("Above KES 5,000,000 · Open Tender admissible");
	});

	it("renders Preference and structure with the helper and reveals the conditional fields", async () => {
		const w = make();
		const card = w.find('[data-testid="ppi-preference"]');
		expect(card.findAll("label").map((l) => l.text())).toEqual(["Preference and reservation", "Plan horizon", "Aggregation", "Lotting"]);
		expect(card.text()).toContain("Recorded for the entity's 30% target. Choose None only where no reservation applies.");
		expect(w.find('[data-testid="ppi-multi-year"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-reservation-reason"]').exists()).toBe(false);
		await w.find('[data-testid="ppi-horizon"]').setValue("Multi-year");
		expect(w.find('[data-testid="ppi-multi-year"]').exists()).toBe(true);
		await w.find('[data-testid="ppi-lotting"]').setValue("Packaged into lots");
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(true);
		// a lower-advantage scheme than the year's highest needs a reason (invariant 24aa)
		await w.find('[data-testid="ppi-reservation"]').setValue("Women");
		expect(w.find('[data-testid="ppi-reservation-reason"]').exists()).toBe(true);
		await w.find('[data-testid="ppi-reservation"]').setValue("Youth");
		expect(w.find('[data-testid="ppi-reservation-reason"]').exists()).toBe(false);
	});

	it("computes the seven baseline dates from the target date and periods, live, before any save (PLN-AC-115)", async () => {
		const w = make();
		const card = w.find('[data-testid="ppi-baseline"]');
		expect(card.find(".pln-card-subhead").text()).toContain("Computed from your target invitation date");
		expect(card.find('[data-testid="ppi-target-date"]').element.value).toBe("2027-05-01");
		const dates = () => card.findAll('[data-testid="ppi-baseline-table"] tbody tr').map((r) => r.findAll("td")[1].text());
		expect(dates()).toEqual([
			"1 May 2027", "22 May 2027", "21 Jun 2027", "26 Jun 2027", "28 Jun 2027", "12 Jul 2027",
			"31 Aug 2027 · from the authorised Requisition",
		]);
		expect(card.text()).toContain("Delivery completion is the department's own required-by date.");
		// closed disclosure with the summary line, no period inputs painted
		expect(w.find('[data-testid="ppi-periods-summary"]').text()).toBe("Using governed defaults for Services · Open Tender");
		expect(w.find('[data-testid="ppi-periods"]').exists()).toBe(false);
		// moving the target date recomputes immediately
		await card.find('[data-testid="ppi-target-date"]').setValue("2027-05-15");
		expect(dates()[1]).toBe("5 Jun 2027");
		expect(dates()[5]).toBe("26 Jul 2027");
		// opening the disclosure and changing a period recomputes too
		await w.find('[data-testid="ppi-adjust-periods"]').trigger("click");
		expect(w.find('[data-testid="ppi-periods"]').findAll("label").map((l) => l.text())).toEqual([
			"Tendering period", "Evaluation period", "Award approval buffer", "Notification buffer", "Standstill period",
		]);
		expect(w.find('[data-testid="ppi-periods"]').text()).toContain("21 days · minimum 7");
		expect(w.find('[data-testid="ppi-periods"]').text()).toContain("30 days · maximum 30");
		expect(w.find('[data-testid="ppi-periods"]').text()).toContain("governed default for this category and method, not a statutory figure");
		await w.find('[data-testid="ppi-tendering_period_days"]').setValue("7");
		expect(dates()[1]).toBe("22 May 2027");
		expect(w.find('[data-testid="ppi-boundary-warning"]').exists()).toBe(false);
	});

	it("warns when the computed signing date leaves no delivery period (invariant 12a)", async () => {
		const w = make();
		await w.find('[data-testid="ppi-target-date"]').setValue("2027-08-20");
		expect(w.find('[data-testid="ppi-boundary-warning"]').exists()).toBe(true);
	});

	it("emits save with exactly the §12.8 inputs — never a milestone date", async () => {
		const w = make();
		await w.find('[data-testid="ppi-title"]').setValue("Renamed package");
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const [payload] = w.emitted("save")[0];
		expect(payload.title).toBe("Renamed package");
		expect(payload.strategic_objective).toBe("OBJ-1");
		expect(payload.procurement_method).toBe("Open Tender");
		expect(payload.baseline_invitation_date).toBe("2027-05-01");
		expect(payload.tendering_period_days).toBe(21);
		expect(payload.standstill_period_days).toBe(14);
		expect(Object.keys(payload).some((k) => /_date$/.test(k) && k !== "baseline_invitation_date")).toBe(false);
		expect(payload).not.toHaveProperty("aggregation_reason");
		expect(payload).not.toHaveProperty("multi_year_justification");
	});

	it("marks the control a readiness blocker names (PLN-AC-114)", () => {
		const w = make({ ...SINGLE, blockers: [{ code: "PLN_STANDSTILL_BELOW_MINIMUM", field: "standstill_period_days" }, { code: "PLN_OBJECTIVE_INELIGIBLE", field: "strategic_objective" }] });
		expect(w.find('[data-testid="ppi-objective"]').attributes("aria-invalid")).toBe("true");
		expect(w.find('[data-testid="ppi-method"]').attributes("aria-invalid")).toBeUndefined();
	});

	it("carries Back, Dissolve and Save draft and no Finance, forecast or actual control (§11.10)", () => {
		const w = make();
		const footer = w.find(".pln-footer-bar");
		expect(footer.findAll("button").map((b) => b.text())).toEqual(["Back to Annual Plan", "Dissolve Plan Item", "Save draft"]);
		expect(w.text()).not.toContain("Finance");
		expect(w.text()).not.toContain("Forecast");
		expect(w.text()).not.toContain("Actual");
		expect(w.find('input[type="date"][data-testid^="ppi-"]:not([data-testid="ppi-target-date"])').exists()).toBe(false);
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

describe("PlanItemEditorScreen — PLN-DES-09A combined", () => {
	it("renders the sources table with its caption and the aggregation reason below Requirement type", () => {
		const w = make(COMBINED);
		const sources = w.find('[data-testid="ppi-sources"]');
		expect(sources.find(".kt-card-title").text()).toBe("Departmental sources");
		expect(sources.findAll("thead th").map((th) => th.text())).toEqual([
			"Requirement", "Department", "Source origin", "Quantity", "Required by", "Procurement Budget Line", "Amount",
		]);
		expect(sources.findAll("tbody tr")).toHaveLength(2);
		expect(sources.text()).toContain("2 sources · 500 each · KES 120,000,000");
		expect(w.find('[data-testid="ppi-source"]').exists()).toBe(false);
		const identity = w.find('[data-testid="ppi-identity"]');
		expect(identity.findAll("label").map((l) => l.text())).toEqual(["Plan Item title", "Procurement description", "Requirement type", "Aggregation reason"]);
		expect(w.find('[data-testid="ppi-aggregation"]').element.value).toContain("Procure one standard laptop specification");
		expect(w.find('[data-testid="ppi-aggregation-indicator"]').element.value).toBe("Aggregated into this package");
	});

	it("emits save including the aggregation reason", async () => {
		const w = make(COMBINED);
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const [payload] = w.emitted("save")[0];
		expect(payload.aggregation_reason).toContain("Procure one standard laptop specification");
	});
});
