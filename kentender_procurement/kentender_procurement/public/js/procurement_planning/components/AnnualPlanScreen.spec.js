// PLN-CHG-001 v1.2 §15.1(5) — AnnualPlanScreen component tests (decision D9).
// Exact fields and the empty state for PLN-DES-07.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AnnualPlanScreen from "./AnnualPlanScreen.vue";

const PLAN = {
	outcome: "OK",
	plan_reference: "PLN-MOH-2027-001",
	version_reference: "PLN-MOH-2027-001-V1",
	record_version: 0,
	mutable: true,
	header: {
		eyebrow: "ANNUAL PROCUREMENT PLAN",
		title: "Ministry of Health Annual Procurement Plan 2027/28",
		reference_line: "PLN-MOH-2027-001 · Version 1",
		badge: "Draft",
	},
	summary: { accepted_entries: 1, allocated: 0, plan_items: 0, value_display: "KES 0" },
	unallocated_sources: [
		{
			dpp_entry: "DPER-1", title: "National digital health infrastructure upgrade",
			department: "Digital Health", source_origin: "Accepted Departmental Need",
			classification: "Non-consulting services", quantity_display: "1 programme",
			budget_line: "MOH-BL-DHI-2027", amount_display: "KES 80,000,000",
		},
	],
	unallocated_caption: "1 entry available",
	plan_items: [],
};

function make(plan = PLAN) {
	return mount(AnnualPlanScreen, { props: { plan, pending: false, errorSummary: "" } });
}

describe("AnnualPlanScreen — PLN-DES-07", () => {
	it("renders the exact summary strip and unallocated-sources row", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("ANNUAL PROCUREMENT PLAN");
		expect(w.find('[data-testid="pln-plan-summary-strip"]').text()).toContain("KES 0");
		const row = w.find('[data-testid="pln-unallocated-sources"] tbody tr');
		expect(row.text()).toContain("National digital health infrastructure upgrade");
		expect(row.text()).toContain("Non-consulting services");
		expect(w.text()).toContain("1 entry available");
	});

	it("shows the empty state with no invented Plan Items", () => {
		const w = make();
		expect(w.find('[data-testid="pln-plan-items"]').text()).toContain("No Plan Items yet");
		expect(w.find('[data-testid="pln-plan-items"] table').exists()).toBe(false);
	});

	it("offers Form Plan Items only while a source is unallocated and the plan is mutable", async () => {
		const withItems = make({ ...PLAN, unallocated_sources: [] });
		expect(withItems.find('[data-testid="pln-form-items"]').exists()).toBe(false);

		const full = make();
		await full.find('[data-testid="pln-form-items"]').trigger("click");
		expect(full.emitted("open-form-dialog")).toHaveLength(1);
	});

	it("renders formed Plan Items and flags a source-correction-required row", () => {
		const w = make({
			...PLAN,
			plan_items: [
				{
					plan_item_id: "PPI-1", title: "A package", requirement_type: "Goods",
					sources: 1, value_display: "KES 1,000,000", finance_state: "Not requested",
					item_state: "Draft", source_correction_required: true,
					route: ["procurement-plan-item", "PPI-1"],
				},
			],
		});
		const row = w.find('[data-testid="pln-item-PPI-1"]');
		expect(row.text()).toContain("Source correction required");
		row.trigger("click");
	});

	it("the Submit consolidated Plan button is disabled until every item is Confirmed (DES-07)", () => {
		const w = make();
		expect(w.find('[data-testid="pln-submit-consolidated"]').attributes("disabled")).toBeDefined();
	});

	it("enables Submit consolidated Plan and emits once ready_for_submission is true", async () => {
		const w = make({ ...PLAN, ready_for_submission: true });
		const button = w.find('[data-testid="pln-submit-consolidated"]');
		expect(button.attributes("disabled")).toBeUndefined();
		await button.trigger("click");
		expect(w.emitted("submit-consolidated")).toHaveLength(1);
	});
});
