// REQ-DES-09 Procurement authorisation task (§13.11) — header, lead-
// department line (HoPF-only, multi-department-only), fresh Planning/Budget
// cards, the §5A compatibility table with every row independently named,
// policy justification, validation, submitted-by, and Return/Authorise.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ProcurementTaskScreen from "./ProcurementTaskScreen.vue";

const TASK = {
	task: { task: "RQK-001", status: "Open", record_version: 0 },
	requisition: { requisition: "PRQ-001", requisition_reference: "REQ-MOH-2027-033-001", plan_item_id: "PPI-MOH-2027-033", lead_org_unit: "OU-DHI", lead_org_unit_label: "Digital Health" },
	version: {
		requirement_title: "Clinical training and deployment laptops for digital health rollout",
		version_number: 1,
		drawdown_lines: [
			{ drawdown_line_id: "DL-001", requested_quantity: 100, requested_value: 20_000_000, unit: "Each" },
			{ drawdown_line_id: "DL-002", requested_quantity: 150, requested_value: 30_000_000, unit: "Each" },
		],
	},
	planning_availability: { eligible: true, remaining_quantity: 250, remaining_amount: 50_000_000, unit: "Each" },
	budget_affordability: [{ budget_line: "vt678eghgt", budget_line_label: "MOH-BL-HWD-2027", requested_amount: 50_000_000, available_before: 60_000_000, sufficient: true, shortfall: 0 }],
	compatibility: [
		{ test: "procurement_category", required: "Goods", actual: "Goods", ok: true },
		{ test: "Requirement type", required: "Straightforward IT equipment", actual: "Straightforward IT equipment", ok: true },
		{ test: "Reservation category", required: "None", actual: "None", ok: true },
		{ test: "Lotting indicator", required: "Single lot", actual: "Single lot", ok: true },
		{ test: "Currency", required: "KES", actual: "KES", ok: true },
		{ test: "Award package", required: "One", actual: "One", ok: true },
	],
	objective_label: "OBJ-MOH-2023-001 — Strengthen interoperable national digital health services",
	validation: { blocking_count: 0, warning_count: 1 },
	submitted_by: { name: "Dr Peter Kimani", decided_at: "2027-03-08 09:00:00" },
	contributing_org_unit_labels: { "OU-DHI": "Digital Health", "OU-HRMD": "Human Resources Management and Development" },
	can_act: true,
	can_change_lead_unit: true,
};

function make(overrides = {}) {
	return mount(ProcurementTaskScreen, { props: { task: { ...TASK, ...overrides }, pending: false } });
}

describe("ProcurementTaskScreen — REQ-DES-09", () => {
	it("renders the exact header and lead-department line with its Change action", () => {
		const w = make();
		expect(w.find(".kt-eyebrow").text()).toBe("PROCUREMENT AUTHORISATION");
		expect(w.find(".kt-status").text()).toBe("Submitted to Procurement");
		expect(w.text()).toContain("Lead department:");
		expect(w.text()).toContain("Digital Health");
		expect(w.find('[data-testid="req-change-lead-unit"]').text()).toBe("Change lead department");
	});

	it("hides the Change-lead-department action when only one department contributed", () => {
		const w = make({ can_change_lead_unit: false });
		expect(w.find('[data-testid="req-change-lead-unit"]').exists()).toBe(false);
	});

	it("renders fresh Planning availability and Budget affordability cards with real numbers", () => {
		const w = make();
		expect(w.text()).toContain("Eligible");
		expect(w.text()).toContain("KES 50,000,000.00 and 250 Each remain available");
		expect(w.text()).toContain("MOH-BL-HWD-2027");
		expect(w.text()).toContain("fully available");
	});

	it("renders every §5A compatibility row independently, never a single collapsed flag", () => {
		const w = make();
		const rows = w.findAll('[data-testid="req-compatibility-table"] tbody tr');
		expect(rows).toHaveLength(6);
		expect(rows[0].text()).toContain("procurement_category");
		expect(rows[0].text()).toContain("Goods");
	});

	it("marks a failing compatibility row distinctly", () => {
		const w = make({ compatibility: [{ test: "procurement_category", required: "Goods", actual: "Works", ok: false }] });
		const row = w.find('[data-testid="req-compatibility-table"] tbody tr');
		expect(row.find(".kt-status").classes()).toContain("is-critical");
	});

	it("renders policy justification, validation and submitted-by", () => {
		const w = make();
		expect(w.text()).toContain("Policy justification");
		expect(w.text()).toContain("OBJ-MOH-2023-001");
		expect(w.text()).toContain("0 Blocking · 1 Warning");
		expect(w.text()).toContain("Submitted by Dr Peter Kimani");
	});

	it("has no edit control and emits return/authorise/change-lead-unit", async () => {
		const w = make();
		expect(w.find("input").exists()).toBe(false);
		await w.find('[data-testid="req-task-return"]').trigger("click");
		expect(w.emitted("return")).toBeTruthy();
		await w.find('[data-testid="req-task-authorise"]').trigger("click");
		expect(w.emitted("authorise")).toBeTruthy();
		await w.find('[data-testid="req-change-lead-unit"]').trigger("click");
		expect(w.emitted("change-lead-unit")).toBeTruthy();
	});

	it("disables actions when can_act is false", () => {
		const w = make({ can_act: false });
		expect(w.find('[data-testid="req-task-return"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="req-task-authorise"]').attributes("disabled")).toBeDefined();
	});
});
