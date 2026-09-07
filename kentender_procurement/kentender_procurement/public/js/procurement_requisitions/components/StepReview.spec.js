// REQ-DES-07 Step 5: Review and submit (§13.9) — the result banner (green
// even with a Warning present, never simply "zero findings"), the six
// summary cards, the warning row, and the full preview.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StepReview from "./StepReview.vue";

const EDITOR = {
	requisition: { plan_item_id: "PPI-MOH-2027-033" },
	version: {
		latest_delivery_date: "2027-09-30",
		drawdown_lines: [
			{ drawdown_line_id: "DL-001", requested_quantity: 100, requested_value: 20_000_000 },
			{ drawdown_line_id: "DL-002", requested_quantity: 150, requested_value: 30_000_000 },
		],
	},
	package: {
		items: [
			{ requisition_item_id: "RQI-001", plan_item_line_id: "DL-001", item_name: "Business laptops", quantity: 100, unit: "Each" },
			{ requisition_item_id: "RQI-002", plan_item_line_id: "DL-002", item_name: "Business laptops", quantity: 150, unit: "Each" },
		],
		technical_requirements: Array.from({ length: 11 }, (_, i) => ({ technical_requirement_id: `TECH-${i}`, row_status: "Confirmed", applies_to_scope: "All items" })),
		related_services: [],
		acceptance_requirements: Array.from({ length: 5 }, (_, i) => ({ acceptance_requirement_id: `ACC-${i}` })),
		supporting_materials: [],
	},
	business_need: "Equip clinical training and field deployment staff with a common laptop specification for the national digital health rollout.",
	delivery_location_label: "Ministry of Health Headquarters, Afya House, Nairobi",
	organisation_unit_labels: { "OU-HRMD": "Human Resources Management and Development", "OU-DHI": "Digital Health" },
	drawdown_context: [
		{ drawdown_line_id: "DL-001", organisation_unit_label: "Human Resources Management and Development" },
		{ drawdown_line_id: "DL-002", organisation_unit_label: "Digital Health" },
	],
	validation: {
		blocking_count: 0,
		warning_count: 1,
		findings: [{ code: "DATE_MATCHES_PLAN_COMPLETION", severity: "Warning", step: 1, message: "Delivery date is the same as the latest approved Plan completion date." }],
	},
};

function make(overrides = {}) {
	return mount(StepReview, { props: { editor: { ...EDITOR, ...overrides } } });
}

describe("StepReview — REQ-DES-07", () => {
	it("shows Ready even with a Warning present — readiness is about Blocking findings only", () => {
		const w = make();
		const banner = w.find('[data-testid="req-review-result"]');
		expect(banner.classes()).toContain("is-ready");
		expect(banner.text()).toContain("Ready for departmental submission");
		expect(banner.text()).toContain("0 Blocking · 1 Warning");
	});

	it("shows Not ready when a Blocking finding exists", () => {
		const w = make({ validation: { blocking_count: 1, warning_count: 0, findings: [{ code: "MISSING_ITEM", severity: "Blocking", step: 2, message: "At least one equipment item is required." }] } });
		expect(w.find('[data-testid="req-review-result"]').classes()).toContain("is-blocked");
	});

	it("renders the six summary cards with the exact fixture counts", () => {
		const w = make();
		expect(w.text()).toContain("2 source lines · 250 Each");
		expect(w.text()).toContain("KES 50,000,000.00");
		expect(w.text()).toContain("2 items");
		expect(w.text()).toContain("11 confirmed rows");
		expect(w.text()).toContain("0 rows");
		expect(w.text()).toContain("5 rows");
		expect(w.text()).toContain("0 files");
	});

	it("renders the warning row's exact message", () => {
		const w = make();
		expect(w.find(".req-notice").text()).toBe("Delivery date is the same as the latest approved Plan completion date.");
	});

	it("renders the full preview with every inherited fact", () => {
		const w = make();
		expect(w.text()).toContain("PPI-MOH-2027-033");
		expect(w.text()).toContain("Digital Health · Human Resources Management and Development");
		expect(w.text()).toContain(EDITOR.business_need);
		expect(w.text()).toContain("Ministry of Health Headquarters, Afya House, Nairobi · 2027-09-30");
		expect(w.text()).toContain("Business laptops — 100 Each (Human Resources Management and Development)");
		expect(w.text()).toContain("None"); // supporting materials
	});
});
