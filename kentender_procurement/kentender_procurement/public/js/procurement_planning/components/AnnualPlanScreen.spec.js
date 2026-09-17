// PLN-CHG-001 v1.18 (PLN18-304/307) — AnnualPlanScreen component tests. U07's
// five tabs, including Governance and publication's own U11-HOPF
// preparation-signature card, and the U08 formation trigger; exact fields,
// absent fields, action visibility straight off the server's read model.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AnnualPlanScreen from "./AnnualPlanScreen.vue";

const READINESS = [
	{ check: "Every Plan Item has a Strategic Objective", result: "Not started", kind: "neutral" },
	{ check: "Plan funding confirmed", result: "Not started", kind: "neutral" },
	{ check: "Planned reservation allocation", result: "0.00 planned · target not published", kind: "advisory" },
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
	version_number: 1,
	project_name: "",
	header: {
		eyebrow: "ANNUAL PROCUREMENT PLAN",
		title: "Ministry of Health Annual Procurement Plan 2027/28",
		reference_line: "PLN-MOH-2027-001 · Version 1",
		badge: "Draft",
	},
	summary: {
		accepted_entries: 1, allocated: 0, plan_items: 0, value_display: "KES 0",
		reserved_share_display: "0.00 planned reservation",
		departmental_sources: 1, departments: 1, funding_evidence_state: "Not requested",
		reservation: { target_percent: 30, required: "KES 48,000,000", qualifying: "KES 0", shortfall: "KES 48,000,000", met: false, basis: { available: false } },
	},
	unallocated_sources: [
		{
			dpp_entry: "DPER-1", title: "National digital health infrastructure upgrade",
			department: "Digital Health", source_origin: "Accepted Departmental Need",
			classification: "Non-consulting services", quantity_display: "1 programme", indicative_amount: 80000000,
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
	affordability: null,
	changes: { is_initial: true },
};

function make(plan = PLAN) {
	return mount(AnnualPlanScreen, { props: { plan, pending: false, errorSummary: "" } });
}

describe("AnnualPlanScreen — open task from the record (FU-14)", () => {
	it("renders the holder's open task in the header and emits its route", async () => {
		const w = make({ ...PLAN, open_task: { label: "Open Finance task", route: ["procurement-planning", "finance", "FNT-1"] } });
		const button = w.find('[data-testid="pln-open-task"]');
		expect(button.text()).toBe("Open Finance task");
		await button.trigger("click");
		expect(w.emitted("open-task")[0][0]).toEqual(["procurement-planning", "finance", "FNT-1"]);
		expect(make(PLAN).find('[data-testid="pln-open-task"]').exists()).toBe(false);
	});
});

describe("AnnualPlanScreen — tabs", () => {
	it("renders all five tabs with Overview active first", () => {
		const w = make();
		const tabs = w.findAll('[role="tab"]');
		expect(tabs.map((t) => t.text())).toEqual(["Overview", "Plan Items", "Funding and readiness", "Governance and publication", "Changes"]);
		expect(w.find('[data-testid="pln-tab-overview"]').attributes("aria-selected")).toBe("true");
	});

	it("switches tabs on click, only one panel visible at a time", async () => {
		const w = make();
		expect(w.find('[data-testid="pln-plan-summary-strip"]').exists()).toBe(true);
		await w.find('[data-testid="pln-tab-items"]').trigger("click");
		expect(w.find('[data-testid="pln-tab-items"]').attributes("aria-selected")).toBe("true");
		expect(w.find('[data-testid="pln-plan-summary-strip"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-unallocated-sources"]').exists()).toBe(true);
	});
});

describe("AnnualPlanScreen — Overview tab", () => {
	it("renders the header and the five-field summary strip", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("ANNUAL PROCUREMENT PLAN");
		expect(w.find('[data-testid="pln-plan-badge"]').text()).toBe("Draft");
		const strip = w.find('[data-testid="pln-plan-summary-strip"]');
		expect(strip.findAll("label").map((l) => l.text())).toEqual([
			"Plan Items", "Departmental sources", "Departments", "Planned value", "Funding evidence",
		]);
		expect(strip.text()).toContain("Not requested");
	});

	it("shows Before submission with the first blocker's own message, switching to the Funding tab", async () => {
		const w = make({ ...PLAN, blockers: [{ code: "PLN_RESERVATION_SHORTFALL", message: "Required reservation allocation not met. Required KES 48,000,000, planned KES 0, shortfall KES 48,000,000." }] });
		const card = w.find('[data-testid="pln-before-submission"]');
		expect(card.text()).toContain("Required reservation allocation not met");
		await card.find("button").trigger("click");
		expect(w.find('[data-testid="pln-tab-funding"]').attributes("aria-selected")).toBe("true");
	});

	it("has no Before submission card once there are no blockers", () => {
		expect(make({ ...PLAN, blockers: [] }).find('[data-testid="pln-before-submission"]').exists()).toBe(false);
	});

	it("edits and saves the project name only when it actually changed", async () => {
		const w = make();
		const save = w.find('[data-testid="pln-save-details"]');
		expect(save.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pln-project-name"]').setValue("Digital health infrastructure programme");
		expect(save.attributes("disabled")).toBeUndefined();
		await save.trigger("click");
		expect(w.emitted("save-details")[0][0]).toEqual({ project_name: "Digital health infrastructure programme" });
	});

	it("disables the project name field once the plan is no longer mutable", () => {
		const w = make({ ...PLAN, mutable: false });
		expect(w.find('[data-testid="pln-project-name"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pln-save-details"]').exists()).toBe(false);
	});
});

describe("AnnualPlanScreen — Plan Items tab", () => {
	function openItems(plan) {
		const w = make(plan);
		w.find('[data-testid="pln-tab-items"]').trigger("click");
		return w;
	}

	it("shows the empty Plan Items state with the unallocated table and Form Plan Items", async () => {
		const w = openItems();
		await w.vm.$nextTick();
		expect(w.find('[data-testid="pln-plan-items"]').exists()).toBe(false);
		const card = w.find('[data-testid="pln-unallocated-sources"]');
		expect(card.findAll("thead th").map((th) => th.text())).toEqual([
			"", "Requirement", "Department", "Source origin", "Classification", "Quantity", "Procurement Budget Line", "Amount",
		]);
		await w.find('[data-testid="pln-form-items"]').trigger("click");
		expect(w.emitted("open-form-dialog")).toHaveLength(1);
	});

	it("renders formed Plan Items and flags a source-correction-required row", async () => {
		const w = openItems({
			...PLAN,
			plan_items: [
				{
					plan_item_id: "PPI-1", title: "A package", departments: "Digital Health", requirement_type: "Goods",
					procurement_method: "Open Tender", reservation_category: "None", completion_display: "31 Aug 2027",
					value_display: "KES 1,000,000", item_state: "Draft", source_correction_required: true,
					route: ["procurement-plan-item", "PPI-1"],
				},
			],
			unallocated_sources: [], unallocated_caption: "",
		});
		await w.vm.$nextTick();
		const row = w.find('[data-testid="pln-item-PPI-1"]');
		expect(row.text()).toContain("Source correction required");
		await row.trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-plan-item", "PPI-1"]);
		expect(w.find('[data-testid="pln-unallocated-sources"]').text()).toContain("No unallocated requirements");
		expect(w.find('[data-testid="pln-form-items"]').exists()).toBe(false);
	});

	it("shows no accepted departmental entries when there is nothing at all", async () => {
		const w = openItems({ ...PLAN, unallocated_sources: [], unallocated_caption: "", plan_items: [] });
		await w.vm.$nextTick();
		expect(w.find('[data-testid="pln-unallocated-sources"]').text()).toContain("No accepted departmental entries");
	});
});

describe("AnnualPlanScreen — Funding and readiness tab", () => {
	function openFunding(plan) {
		const w = make(plan);
		w.find('[data-testid="pln-tab-funding"]').trigger("click");
		return w;
	}

	it("renders the Budget table when affordability is available", async () => {
		const w = openFunding({
			...PLAN,
			affordability: {
				within_approved: true,
				lines: [{ budget_line: "BL-1", reference: "MOH-BL-DHI-2027", title: "Digital health infrastructure programme", funding_source: "Government of Kenya", approved: 100000000, planned: 80000000, reserved: 0, committed: 0, available: 100000000 }],
			},
		});
		await w.vm.$nextTick();
		const card = w.find('[data-testid="pln-budget-table"]');
		expect(card.findAll("thead th").map((th) => th.text())).toEqual([
			"Budget Line", "Funding source", "Approved", "Planned", "Reserved", "Committed", "Available",
		]);
		expect(card.text()).toContain("Within approved amounts");
	});

	it("has no Budget table when affordability has not been computed", async () => {
		const w = openFunding({ ...PLAN, affordability: null });
		await w.vm.$nextTick();
		expect(w.find('[data-testid="pln-budget-table"]').exists()).toBe(false);
	});

	it("renders the Reservation card and the plan readiness rows", async () => {
		const w = openFunding();
		await w.vm.$nextTick();
		const reservation = w.find('[data-testid="pln-reservation"]');
		expect(reservation.text()).toContain("Required allocation not met");
		expect(reservation.findAll(".kt-label").map((l) => l.text())).toEqual([
			"Target", "Required allocation", "Planned qualifying allocation", "Shortfall",
		]); // no Budget basis fact: basis.available is false in the fixture
		const readiness = w.find('[data-testid="pln-readiness"]');
		expect(readiness.findAll("tbody tr")).toHaveLength(READINESS.length);
	});

	it("offers the splitting confirmation only while an advisory is unconfirmed (O1)", async () => {
		const w = openFunding({
			...PLAN,
			readiness: READINESS.map((r) => (r.check === "Contract splitting review" ? { ...r, result: "1 advisory", kind: "advisory" } : r)),
			splitting_advisories: [{ message: "Two items on MOH-BL-DHI-2027 together exceed the open-tender threshold." }],
		});
		await w.vm.$nextTick();
		await w.find('[data-testid="pln-confirm-splitting"]').trigger("click");
		expect(w.emitted("confirm-splitting")).toHaveLength(1);
		expect(w.find('[data-testid="pln-splitting-advisories"]').text()).toContain("together exceed");
	});

	it("keeps Request plan funding confirmation disabled until the server says ready", async () => {
		const w = openFunding();
		await w.vm.$nextTick();
		expect(w.find('[data-testid="pln-request-funding"]').attributes("disabled")).toBeDefined();
	});

	it("emits the version-level funding request once enabled", async () => {
		const w = openFunding({ ...PLAN, can_request_funding: true });
		await w.vm.$nextTick();
		await w.find('[data-testid="pln-request-funding"]').trigger("click");
		expect(w.emitted("request-funding")).toHaveLength(1);
	});
});

describe("AnnualPlanScreen — Governance and publication tab", () => {
	// U11-HOPF (§9's "Existing Plan record for preparation") — Charles's own
	// preparation-signature card lives here, on the Draft record's own route;
	// no Adopt/Approve/Board controls (those belong to ReviewScreen's own
	// task route once a governance task exists).
	it("shows the preparation-signature card, no Adopt or Approve controls", async () => {
		const w = make();
		await w.find('[data-testid="pln-tab-governance"]').trigger("click");
		const card = w.find('[data-testid="pln-preparation-decisions"]');
		expect(card.text()).toContain("No Preparation decision recorded yet.");
		expect(card.text()).toContain("I confirm that the complete Annual Procurement Plan Version 1 is ready for Accounting Officer adoption.");
		expect(w.text()).not.toContain("Adopt");
		expect(w.text()).not.toContain("Approve");
	});
});

describe("AnnualPlanScreen — Changes tab", () => {
	it("shows No earlier Version for the initial Version", async () => {
		const w = make({ ...PLAN, changes: { is_initial: true } });
		await w.find('[data-testid="pln-tab-changes"]').trigger("click");
		const card = w.find('[data-testid="pln-changes"]');
		expect(card.text()).toContain("No earlier Version");
		expect(card.text()).toContain("This is the first Version of the Annual Plan.");
	});

	it("shows the change reason and the Unchanged facts for a narrative-only update", async () => {
		const w = make({
			...PLAN,
			changes: { is_initial: false, based_on_version_number: 1, change_reason: "Clarify the infrastructure scope for the priority facilities identified.", source_set_changed: false, quantities_changed: false, value_changed: false },
		});
		await w.find('[data-testid="pln-tab-changes"]').trigger("click");
		const card = w.find('[data-testid="pln-changes"]');
		expect(card.text()).toContain("Clarify the infrastructure scope");
		expect(card.findAll(".kt-label").map((l) => l.text())).toEqual(["Source set", "Quantities", "Value"]);
		expect(card.text().match(/Unchanged/g)).toHaveLength(3);
	});
});

describe("AnnualPlanScreen — footer", () => {
	it("hides the submit footer once the plan is no longer mutable or awaiting confirmation", () => {
		expect(make({ ...PLAN, mutable: false, funding_state: "Confirmed" }).find('[data-testid="pln-submit-consolidated"]').exists()).toBe(false);
	});

	it("emits the submission once enabled, always labelled Sign and submit Annual Plan", async () => {
		const w = make({ ...PLAN, can_submit: true });
		const button = w.find('[data-testid="pln-submit-consolidated"]');
		expect(button.text()).toBe("Sign and submit Annual Plan");
		await button.trigger("click");
		expect(w.emitted("submit-consolidated")).toHaveLength(1);
	});

	it("keeps the same label for a correction's resubmission (v1.18 §6.2 — one existing action)", () => {
		const w = make({ ...PLAN, can_submit: true, is_correction: true });
		expect(w.find('[data-testid="pln-submit-consolidated"]').text()).toBe("Sign and submit Annual Plan");
	});

	it("states the funding state plainly while awaiting, returned or stale", () => {
		expect(make({ ...PLAN, funding_state: "Awaiting confirmation", mutable: false }).find('[data-testid="pln-funding-notice"]').text()).toContain("Awaiting Finance confirmation");
		expect(make({ ...PLAN, funding_state: "Returned" }).find('[data-testid="pln-funding-notice"]').text()).toContain("returned by Finance");
		expect(make({ ...PLAN, funding_state: "Stale" }).find('[data-testid="pln-funding-notice"]').text()).toContain("no longer current");
		expect(make().find('[data-testid="pln-funding-notice"]').exists()).toBe(false);
	});

	it("shows no charts or blank-item creation control anywhere (§11.8)", () => {
		const w = make();
		expect(w.find("canvas").exists()).toBe(false);
		expect(w.text()).not.toContain("New Plan Item");
	});
});
