// PLN-CHG-001 v1.12 §15 — AnnualPlanScreen component tests (D14). Exact
// fields, the nine-row readiness card, the empty state and the footer's
// version-level funding request for PLN-DES-07.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AnnualPlanScreen from "./AnnualPlanScreen.vue";

const READINESS = [
	{ check: "Every Plan Item has a Strategic Objective", result: "Not started", kind: "neutral" },
	{ check: "Every Plan Item has a reservation category", result: "Not started", kind: "neutral" },
	{ check: "Every Plan Item records plan horizon, aggregation and lotting", result: "Not started", kind: "neutral" },
	{ check: "Baseline schedule meets the governed periods and delivery boundary", result: "Not started", kind: "neutral" },
	{ check: "Procurement method admissible for value", result: "Not started", kind: "neutral" },
	{ check: "Plan within approved budget", result: "Not started", kind: "neutral" },
	{ check: "Plan funding confirmed", result: "Not started", kind: "neutral" },
	{ check: "Preference and reservation target", result: "0% of plan value reserved · target 30%", kind: "advisory" },
	{ check: "Contract splitting review", result: "No advisory", kind: "neutral" },
];

const PLAN = {
	outcome: "OK",
	plan_reference: "PLN-MOH-2027-001",
	version_reference: "PLN-MOH-2027-001-V1",
	record_version: 0,
	mutable: true,
	can_act: true,
	funding_state: "Not requested",
	is_correction: false,
	header: {
		eyebrow: "ANNUAL PROCUREMENT PLAN",
		title: "Ministry of Health Annual Procurement Plan 2027/28",
		reference_line: "PLN-MOH-2027-001 · Version 1",
		badge: "Draft",
	},
	summary: {
		accepted_entries: 1, allocated: 0, plan_items: 0, value_display: "KES 0",
		reserved_share_display: "0% of plan value · target 30%",
	},
	unallocated_sources: [
		{
			dpp_entry: "DPER-1", title: "National digital health infrastructure upgrade",
			department: "Digital Health", source_origin: "Accepted Departmental Need",
			classification: "Non-consulting services", quantity_display: "1 programme",
			budget_line: "BL-1", budget_line_display: "MOH-BL-DHI-2027", amount_display: "KES 80,000,000",
		},
	],
	unallocated_caption: "1 entry available",
	plan_items: [],
	readiness: READINESS,
	blockers: [],
	splitting_advisories: [],
	splitting_confirmation: "",
	can_request_funding: false,
	can_submit: false,
	late_activation_required: false,
};

function make(plan = PLAN) {
	return mount(AnnualPlanScreen, { props: { plan, pending: false, errorSummary: "" } });
}

describe("AnnualPlanScreen — PLN-DES-07", () => {
	it("renders the header, the five-field strip with Reserved share and the unallocated row", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("ANNUAL PROCUREMENT PLAN");
		expect(w.find('[data-testid="pln-plan-badge"]').text()).toBe("Draft");
		const strip = w.find('[data-testid="pln-plan-summary-strip"]');
		expect(strip.findAll("label").map((l) => l.text())).toEqual([
			"Accepted departmental entries", "Allocated", "Plan Items", "Plan value", "Reserved share",
		]);
		expect(w.find('[data-testid="pln-reserved-share"]').text()).toBe("0% of plan value · target 30%");
		const card = w.find('[data-testid="pln-unallocated-sources"]');
		expect(card.findAll("thead th").map((th) => th.text())).toEqual([
			"Requirement", "Department", "Source origin", "Classification", "Quantity", "Procurement Budget Line", "Amount", "Status",
		]);
		const row = card.find("tbody tr");
		expect(row.text()).toContain("MOH-BL-DHI-2027");
		expect(row.find(".kt-status").text()).toBe("Unallocated");
		expect(w.text()).toContain("1 entry available");
	});

	it("shows the empty Plan Items state with no invented rows", () => {
		const w = make();
		expect(w.find('[data-testid="pln-plan-items"] h3').text()).toBe("No Plan Items yet");
		expect(w.find('[data-testid="pln-plan-items"]').text()).toContain("Form Plan Items from the accepted departmental entries above.");
		expect(w.find('[data-testid="pln-plan-items"] table').exists()).toBe(false);
	});

	it("renders the nine readiness rows with their exact copy and badge treatments", () => {
		const w = make();
		const card = w.find('[data-testid="pln-readiness"]');
		expect(card.find(".kt-card-title").text()).toBe("Plan readiness");
		expect(card.findAll("thead th").map((th) => th.text())).toEqual(["Check", "Result"]);
		const rows = card.findAll("tbody tr");
		expect(rows).toHaveLength(9);
		expect(rows.map((r) => r.find("td").text())).toEqual(READINESS.map((r) => r.check));
		expect(rows[0].find(".kt-status").classes()).toContain("is-pending");
		expect(rows[7].find(".kt-status").classes()).toContain("is-attention");
		expect(rows[7].find(".kt-status").text()).toBe("0% of plan value reserved · target 30%");
		expect(rows[8].find(".kt-status").text()).toBe("No advisory");
		expect(w.find('[data-testid="pln-confirm-splitting"]').exists()).toBe(false);
	});

	it("offers the splitting confirmation only while an advisory is unconfirmed (O1)", async () => {
		const w = make({
			...PLAN,
			readiness: READINESS.map((r) => (r.check === "Contract splitting review" ? { ...r, result: "1 advisory", kind: "advisory" } : r)),
			splitting_advisories: [{ message: "Two items on MOH-BL-DHI-2027 together exceed the open-tender threshold." }],
		});
		await w.find('[data-testid="pln-confirm-splitting"]').trigger("click");
		expect(w.emitted("confirm-splitting")).toHaveLength(1);
		expect(w.find('[data-testid="pln-splitting-advisories"]').text()).toContain("together exceed");
		const confirmed = make({ ...PLAN, splitting_advisories: [{ message: "x" }], splitting_confirmation: "Legitimately separate." });
		expect(confirmed.find('[data-testid="pln-confirm-splitting"]').exists()).toBe(false);
	});

	it("offers Form Plan Items only while a source is unallocated and the plan is mutable", async () => {
		const withItems = make({ ...PLAN, unallocated_sources: [], unallocated_caption: "" });
		expect(withItems.find('[data-testid="pln-form-items"]').exists()).toBe(false);
		expect(withItems.find('[data-testid="pln-no-sources"] h3').text()).toBe("No accepted departmental entries");
		const full = make();
		await full.find('[data-testid="pln-form-items"]').trigger("click");
		expect(full.emitted("open-form-dialog")).toHaveLength(1);
	});

	it("renders formed Plan Items and flags a source-correction-required row", () => {
		const w = make({
			...PLAN,
			plan_items: [
				{
					plan_item_id: "PPI-1", title: "A package", departments: "Digital Health", requirement_type: "Goods",
					procurement_method: "Open Tender", reservation_category: "None", completion_display: "31 Aug 2027",
					value_display: "KES 1,000,000", item_state: "Draft", source_correction_required: true,
					route: ["procurement-plan-item", "PPI-1"],
				},
			],
		});
		const row = w.find('[data-testid="pln-item-PPI-1"]');
		expect(row.text()).toContain("Source correction required");
		row.trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-plan-item", "PPI-1"]);
	});

	it("keeps both footer actions disabled until the server says the plan is ready (§11.8)", () => {
		const w = make();
		expect(w.find('[data-testid="pln-request-funding"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pln-submit-consolidated"]').attributes("disabled")).toBeDefined();
		expect(w.text()).not.toContain("Request Finance confirmation");
	});

	it("emits the version-level funding request and the submission once enabled", async () => {
		const w = make({ ...PLAN, can_request_funding: true, can_submit: true });
		await w.find('[data-testid="pln-request-funding"]').trigger("click");
		expect(w.emitted("request-funding")).toHaveLength(1);
		await w.find('[data-testid="pln-submit-consolidated"]').trigger("click");
		expect(w.emitted("submit-consolidated")).toHaveLength(1);
	});

	it("states the funding state plainly while awaiting, returned or stale", () => {
		expect(make({ ...PLAN, funding_state: "Awaiting Finance", mutable: false }).find('[data-testid="pln-funding-notice"]').text()).toContain("Awaiting Finance confirmation");
		expect(make({ ...PLAN, funding_state: "Returned" }).find('[data-testid="pln-funding-notice"]').text()).toContain("returned by Finance");
		expect(make({ ...PLAN, funding_state: "Stale" }).find('[data-testid="pln-funding-notice"]').text()).toContain("no longer current");
		expect(make().find('[data-testid="pln-funding-notice"]').exists()).toBe(false);
	});

	it("shows no charts, blank-item creation, per-item Finance or approval controls (§11.8)", () => {
		const w = make();
		expect(w.find("canvas").exists()).toBe(false);
		expect(w.text()).not.toContain("New Plan Item");
		expect(w.text()).not.toContain("Adopt");
		expect(w.text()).not.toContain("Approve");
	});
});
