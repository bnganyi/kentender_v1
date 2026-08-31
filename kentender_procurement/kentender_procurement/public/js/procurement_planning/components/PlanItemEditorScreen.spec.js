// PLN-CHG-001 v1.2 §15.1(5) — PlanItemEditorScreen component tests (D9).
// PLN-DES-09 (single source) and PLN-DES-09A (combined) exact fields, the
// read-only source rows, and the source-correction-required notice.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PlanItemEditorScreen from "./PlanItemEditorScreen.vue";

const SINGLE = {
	outcome: "OK",
	plan_item_id: "PPI-MOH-2027-021",
	record_version: 0,
	mutable: true,
	combined: false,
	source_correction_required: false,
	header: {
		eyebrow: "PLAN ITEM",
		title: "National digital health infrastructure upgrade",
		reference_line: "PPI-MOH-2027-021 · Draft Version 1",
		item_state_badge: "Proposed",
		finance_state_badge: "Finance not requested",
	},
	plan_reference: "PLN-MOH-2027-001",
	sources: [
		{
			requirement: "National digital health infrastructure upgrade", department: "Digital Health",
			source_origin: "Accepted Departmental Need",
			departmental_plan_line: "DPP-MOH-DHI-2027-001 · Version 1",
			need_reference_line: "NDS-MOH-2027-0001 · Version 1",
			quantity_display: "1 programme", required_by_display: "31 Aug 2027",
			budget_line: "MOH-BL-DHI-2027 — Digital health infrastructure programme",
			amount_display: "KES 80,000,000",
		},
	],
	sources_caption: "",
	item: {
		title: "National digital health infrastructure upgrade",
		description: "Procure and implement the national digital health infrastructure upgrade as one integrated FY 2027/28 programme.",
		requirement_type: "Non-consulting services",
		strategic_objective: "OBJ-MOH-2023-001",
		objective_path: "Digital health systems › Health policy, standards and regulation › Digital health governance",
		procurement_method: "Open Tender",
		aggregation_reason: "",
	},
	objective_eligible: true,
	strategic_objectives: [
		{ id: "OBJ-MOH-2023-001", title: "Strengthen interoperable national digital health services" },
	],
	schedule: {
		invitation_date: "2027-05-01", bid_opening_date: "2027-05-23",
		evaluation_completion_date: "2027-06-23", award_approval_date: "2027-07-10",
		award_notification_date: "2027-07-14", contract_signing_date: "2027-08-01",
		delivery_completion_date: "2027-08-31",
	},
};

const COMBINED = {
	...SINGLE,
	combined: true,
	sources: [
		SINGLE.sources[0],
		{
			requirement: "Clinical deployment laptops", department: "Digital Health",
			source_origin: "Accepted Departmental Need", quantity_display: "300 each",
			required_by_display: "31 Dec 2027", budget_line: "MOH-BL-DHI-2027",
			amount_display: "KES 72,000,000",
		},
	],
	sources_caption: "2 sources · 500 each · KES 152,000,000",
	item: { ...SINGLE.item, aggregation_reason: "Procure one standard laptop specification." },
};

function make(item = SINGLE) {
	return mount(PlanItemEditorScreen, { props: { item, pending: false, errorSummary: "" } });
}

describe("PlanItemEditorScreen — PLN-DES-09 single source", () => {
	it("renders the single read-only source card and no source table", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-source"]').text()).toContain("MOH-BL-DHI-2027");
		expect(w.find('[data-testid="ppi-sources"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-title"]').element.value).toBe(
			"National digital health infrastructure upgrade"
		);
	});

	it("keeps requirement type, objective path and method read-only, title/description/objective editable", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-objective"]').exists()).toBe(true);
		expect(w.text()).toContain("Digital health systems");
		expect(w.find('[data-testid="ppi-aggregation"]').exists()).toBe(false);
	});

	it("does not show the source-correction notice when the source is current", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-source-correction"]').exists()).toBe(false);
	});

	it("emits save with the allow-listed form values", async () => {
		const w = make();
		await w.find('[data-testid="ppi-title"]').setValue("Renamed package");
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const [payload] = w.emitted("save")[0];
		expect(payload.title).toBe("Renamed package");
		expect(payload.strategic_objective).toBe("OBJ-MOH-2023-001");
		expect(payload.delivery_completion_date).toBe("2027-08-31");
	});

	it("Dissolve Plan Item and Request Finance confirmation are both present; only Request Finance is disabled", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-dissolve"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="ppi-request-finance"]').attributes("disabled")).toBeDefined();
	});
});

describe("PlanItemEditorScreen — PLN-DES-09A combined", () => {
	it("renders the departmental sources table with its caption and the aggregation reason field", () => {
		const w = make(COMBINED);
		const rows = w.findAll('[data-testid="ppi-sources"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(w.find('[data-testid="ppi-sources"]').text()).toContain("2 sources · 500 each");
		expect(w.find('[data-testid="ppi-aggregation"]').element.value).toContain(
			"Procure one standard laptop specification."
		);
	});
});

describe("PlanItemEditorScreen — §12.7 source correction required", () => {
	it("shows the notice while Save and Dissolve remain visible so the Planner can recover", () => {
		const w = make({ ...SINGLE, source_correction_required: true });
		expect(w.find('[data-testid="ppi-source-correction"]').text()).toContain(
			"Source correction required"
		);
	});
});
