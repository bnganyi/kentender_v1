// REQ-DES-08 Department approval task (§13.10) — read-only certification
// screen: header, three summary cards, drawdown/items/technical tables,
// content digest, the certification statement, and Return/Submit footer.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DepartmentTaskScreen from "./DepartmentTaskScreen.vue";

const TASK = {
	task: { task: "RQT-001", status: "Open", record_version: 0 },
	requisition: { requisition: "PRQ-001", requisition_reference: "REQ-MOH-2027-033-001", plan_item_id: "PPI-MOH-2027-033" },
	version: {
		requirement_title: "Clinical training and deployment laptops for digital health rollout",
		version_number: 1,
		content_digest: "3f9a1c7e2b04",
		drawdown_lines: [
			{ drawdown_line_id: "DL-001", requested_quantity: 100, requested_value: 20_000_000 },
			{ drawdown_line_id: "DL-002", requested_quantity: 150, requested_value: 30_000_000 },
		],
	},
	package: {
		content_digest: "8ab21f",
		items: [
			{ requisition_item_id: "RQI-001", item_name: "Business laptops", equipment_category: "Laptop", quantity: 100, unit: "Each", intended_use: "Clinical training for HRMD staff" },
			{ requisition_item_id: "RQI-002", item_name: "Business laptops", equipment_category: "Laptop", quantity: 150, unit: "Each", intended_use: "Field deployment for Digital Health staff" },
		],
		technical_requirements: [
			{ technical_requirement_id: "TECH-001", characteristic_key: "electrical_compatibility", row_status: "Confirmed", required_value_display: "Yes" },
			{ technical_requirement_id: "TECH-002", characteristic_key: "memory", row_status: "Confirmed", required_value_display: "16 GB" },
		],
	},
	drawdown_context: [
		{ drawdown_line_id: "DL-001", organisation_unit: "OU-HRMD", organisation_unit_label: "Human Resources Management and Development", source_title: "Business laptops", unit: "Each" },
		{ drawdown_line_id: "DL-002", organisation_unit: "OU-DHI", organisation_unit_label: "Digital Health", source_title: "Business laptops", unit: "Each" },
	],
	prepared_by: { name: "Grace Wanjiku", role: "Departmental Author" },
	catalogue: { characteristics: [{ key: "electrical_compatibility", label: "Electrical compatibility" }, { key: "memory", label: "Memory" }] },
	validation: { blocking_count: 0, warning_count: 1 },
	can_act: true,
	can_certify: true,
	can_return: true,
};

function make(overrides = {}) {
	return mount(DepartmentTaskScreen, { props: { task: { ...TASK, ...overrides }, actorName: "Dr Peter Kimani", actorRoleLabel: "Head of User Department for Digital Health", pending: false } });
}

describe("DepartmentTaskScreen — REQ-DES-08", () => {
	it("renders the exact header: eyebrow, title, status, reference, prepared-by", () => {
		const w = make();
		expect(w.find(".kt-eyebrow").text()).toBe("DEPARTMENT APPROVAL");
		expect(w.find(".req-editor-title").text()).toBe("Clinical training and deployment laptops for digital health rollout");
		expect(w.find(".kt-status").text()).toBe("Awaiting Department Approval");
		expect(w.find(".req-prepared-by").text()).toBe("Prepared by Grace Wanjiku, Departmental Author");
	});

	it("renders the three summary cards with real totals", () => {
		const w = make();
		expect(w.text()).toContain("2 source lines · 250 Each");
		expect(w.text()).toContain("KES 50,000,000.00");
		expect(w.text()).toContain("2 confirmed rows");
		expect(w.text()).toContain("0 Blocking · 1 Warning");
	});

	it("renders the drawdown, items and technical-requirements tables", () => {
		const w = make();
		const drawdownRows = w.findAll('[data-testid="req-task-drawdown-table"] tbody tr');
		expect(drawdownRows).toHaveLength(2);
		expect(drawdownRows[0].text()).toContain("Human Resources Management and Development");
		expect(drawdownRows[0].text()).toContain("100 Each");
		const itemRows = w.findAll('[data-testid="req-task-items-table"] tbody tr');
		expect(itemRows).toHaveLength(2);
		const techRows = w.findAll('[data-testid="req-task-technical-table"] tbody tr');
		expect(techRows).toHaveLength(2);
		expect(techRows[1].text()).toContain("Memory");
		expect(techRows[1].text()).toContain("16 GB");
	});

	it("renders the content digest and the certification statement with the deciding actor", () => {
		const w = make();
		expect(w.text()).toContain("Content digest");
		expect(w.text()).toContain("8ab21f");
		expect(w.find(".req-certification-statement").text()).toBe(
			"I confirm that this Requisition states the departments' operational need and minimum requirements and may be submitted to Procurement."
		);
		expect(w.text()).toContain("Decision by Dr Peter Kimani, Head of User Department for Digital Health — certifying on behalf of both contributing departments.");
	});

	it("has no edit control — only Return and Submit", () => {
		const w = make();
		expect(w.find("input").exists()).toBe(false);
		expect(w.find("textarea").exists()).toBe(false);
		expect(w.find('[data-testid="req-task-return"]').text()).toBe("Return for correction");
		expect(w.find('[data-testid="req-task-submit"]').text()).toBe("Submit to Procurement");
	});

	it("emits return and submit", async () => {
		const w = make();
		await w.find('[data-testid="req-task-return"]').trigger("click");
		expect(w.emitted("return")).toBeTruthy();
		await w.find('[data-testid="req-task-submit"]').trigger("click");
		expect(w.emitted("submit")).toBeTruthy();
	});

	it("disables both actions while a command is pending", () => {
		const w = mount(DepartmentTaskScreen, { props: { task: TASK, actorName: "Dr Peter Kimani", actorRoleLabel: "Head of User Department for Digital Health", pending: true } });
		expect(w.find('[data-testid="req-task-return"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="req-task-submit"]').attributes("disabled")).toBeDefined();
	});

	// KT-STD-001 §3A.6 — an oversight reader (Administrator/System Manager/
	// Auditor) gets `can_certify`/`can_return` both False from the server;
	// the certification screen must hide the decision controls entirely,
	// never merely disable them, and must not attribute the decision to a
	// blank actor.
	it("hides both decision controls and the Decision-by line for an oversight reader", () => {
		const w = mount(DepartmentTaskScreen, { props: { task: { ...TASK, can_certify: false, can_return: false }, actorName: "", actorRoleLabel: "", pending: false } });
		expect(w.find('[data-testid="req-task-return"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-task-submit"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Decision by");
	});
});
