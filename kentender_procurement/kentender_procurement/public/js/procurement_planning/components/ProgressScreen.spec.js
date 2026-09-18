// PLN-CHG-001 v1.23 §10.13 — ProgressScreen component tests (U14).
//
// What is planned, what is covered and what has started — and, just as much,
// what is deliberately absent: no completion column, no forecast column, no
// action to change expected dates, and no summed units.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ProgressScreen from "./ProgressScreen.vue";

function purchase(overrides = {}) {
	const row = {
		plan_item_id: "PPI-MOH-2027-033",
		title: "Clinical training and deployment laptops for digital health rollout",
		planned_display: "250 Each / KES 50,000,000",
		covered_display: "0 Each / KES 0",
		not_covered_display: "250 Each / KES 50,000,000",
		fully_covered: false,
		procurement_stage: "Not started",
		proceedings: [],
		hold: null,
		scope_locked: false,
		...overrides,
	};
	// The route always follows the purchase it belongs to.
	return { ...row, route: ["procurement-plan-item", row.plan_item_id] };
}

function progress(overrides = {}) {
	return {
		outcome: "OK",
		plan_reference: "PLN-MOH-2027-001",
		plan_title: "Ministry of Health Annual Procurement Plan 2027/28",
		version_number: 1,
		status: "Current plan",
		financial_year_label: "FY 2027/28",
		items: [
			purchase({
				plan_item_id: "PPI-MOH-2027-032",
				title: "National digital health infrastructure upgrade",
				planned_display: "1 Programme / KES 80,000,000",
				covered_display: "0 Programme / KES 0",
				not_covered_display: "1 Programme / KES 80,000,000",
			}),
			purchase(),
		],
		...overrides,
	};
}

function make(props = {}) {
	return mount(ProgressScreen, { props: { progress: progress(), pending: false, errorSummary: "", ...props } });
}

describe("ProgressScreen — U14 BASE", () => {
	it("names the plan in force and both purchases with their own units", () => {
		const w = make();
		expect(w.find('[data-testid="prg-context"]').text()).toContain("PLN-MOH-2027-001");
		expect(w.find('[data-testid="prg-context"]').text()).toContain("FY 2027/28");
		expect(w.find('[data-testid="prg-context"]').text()).toContain("Current plan");

		const rows = w.findAll('[data-testid="prg-purchase"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("1 Programme / KES 80,000,000");
		expect(rows[1].text()).toContain("250 Each / KES 50,000,000");
		// Two different units, two separate purchases; nothing adds them up.
		expect(w.text()).not.toContain("251");
	});

	it("says what has started rather than leaving it blank", () => {
		const w = make();
		expect(w.findAll('[data-testid="prg-purchase"]')[0].text()).toContain("Not started");
	});

	it("offers no completion column, no forecast and no date-change action", () => {
		const w = make();
		expect(w.text()).not.toContain("Completion");
		expect(w.text()).not.toContain("Forecast");
		expect(w.text()).not.toContain("Update expected dates");
		expect(w.text()).not.toContain("not yet available");
	});

	it("opens the purchase it names", async () => {
		const w = make();
		await w.findAll('[data-testid="prg-view-purchase"]')[0].trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["procurement-plan-item", "PPI-MOH-2027-032"]);
	});
});

describe("ProgressScreen — coverage", () => {
	it("U14-PARTIAL: covered and not-yet-covered are both quantity and value", () => {
		const w = make({
			progress: progress({
				items: [
					purchase({
						covered_display: "100 Each / KES 20,000,000",
						not_covered_display: "150 Each / KES 30,000,000",
						procurement_stage: "Sourcing",
						proceedings: [
							{
								proceeding_type: "Requisition",
								proceeding_id: "REQ-MOH-2027-015",
								requisition_reference: "REQ-MOH-2027-015",
								covered_display: "100 / KES 20,000,000",
								stage: "Sourcing",
								milestones: [],
								durations: [],
							},
						],
					}),
				],
			}),
		});
		const row = w.find('[data-testid="prg-purchase"]');
		expect(row.text()).toContain("100 Each / KES 20,000,000");
		expect(row.text()).toContain("150 Each / KES 30,000,000");
		expect(row.text()).toContain("Sourcing");
	});

	it("U14-FULL-COVERAGE: each proceeding keeps its own quantity and value", () => {
		const w = make({
			progress: progress({
				items: [
					purchase({
						covered_display: "250 Each / KES 50,000,000",
						not_covered_display: "0 Each / KES 0",
						fully_covered: true,
						proceedings: [
							{ proceeding_id: "REQ-MOH-2027-010", requisition_reference: "REQ-MOH-2027-010", covered_display: "100 / KES 20,000,000", stage: "Published", milestones: [], durations: [] },
							{ proceeding_id: "REQ-MOH-2027-011", requisition_reference: "REQ-MOH-2027-011", covered_display: "150 / KES 30,000,000", stage: "Published", milestones: [], durations: [] },
						],
					}),
				],
			}),
		});
		const proceedings = w.findAll('[data-testid="prg-proceeding"]');
		expect(proceedings).toHaveLength(2);
		expect(proceedings[0].text()).toContain("100 / KES 20,000,000");
		expect(proceedings[1].text()).toContain("150 / KES 30,000,000");
		// Published is a publication state, never a completion claim.
		expect(w.text()).not.toContain("Delivered");
		expect(w.text()).not.toContain("Completed");
	});
});

describe("ProgressScreen — U14-ACTUALS", () => {
	const dated = {
		proceeding_id: "REQ-MOH-2027-015",
		requisition_reference: "REQ-MOH-2027-015",
		covered_display: "100 / KES 20,000,000",
		stage: "Published",
		milestones: [
			{ milestone: "invitation", label: "Invitation or advertisement", approved_display: "15 May 2027", actual_display: "18 May 2027", days_after_approved: "3" },
			{ milestone: "bid_opening", label: "Bid opening", approved_display: "5 Jun 2027", actual_display: "No date recorded", days_after_approved: "—" },
		],
		durations: [],
	};

	it("shows the approved date, the owner's actual and the days between", () => {
		const w = make({ progress: progress({ items: [purchase({ proceedings: [dated] })] }) });
		const rows = w.findAll('[data-testid="prg-milestone-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("15 May 2027");
		expect(rows[0].text()).toContain("18 May 2027");
		expect(rows[0].text()).toContain("3");
		// A supported milestone the owner has not reported says so plainly.
		expect(rows[1].text()).toContain("No date recorded");
	});

	it("omits the durations table until both endpoints exist", () => {
		const w = make({ progress: progress({ items: [purchase({ proceedings: [dated] })] }) });
		expect(w.find('[data-testid="prg-durations"]').exists()).toBe(false);

		const withBoth = make({
			progress: progress({
				items: [purchase({ proceedings: [{ ...dated, durations: [{ from_label: "Invitation or advertisement", to_label: "Bid opening", planned_elapsed_days: "21", actual_elapsed_days: "24", difference_days: "-3" }] }] })],
			}),
		});
		expect(withBoth.find('[data-testid="prg-duration-row"]').text()).toContain("24");
	});

	it("omits the whole dated table for a proceeding no owner has reported on", () => {
		const w = make({
			progress: progress({
				items: [purchase({ proceedings: [{ proceeding_id: "REQ-MOH-2027-015", covered_display: "100 / KES 20,000,000", stage: "Sourcing", milestones: [], durations: [] }] })],
			}),
		});
		expect(w.find('[data-testid="prg-milestones"]').exists()).toBe(false);
	});
});

describe("ProgressScreen — U14-HOLD", () => {
	it("shows the hold in the affected purchase and links to its requests", async () => {
		const w = make({
			progress: progress({
				items: [
					purchase({
						hold: {
							open_requests: 2,
							text: "New requisitions are on hold while these requests remain unresolved.",
							link_text: "View correction requests",
						},
						proceedings: [{ proceeding_id: "REQ-MOH-2027-015", covered_display: "100 / KES 20,000,000", stage: "Stopped", milestones: [], durations: [] }],
					}),
				],
			}),
		});
		const hold = w.find('[data-testid="prg-hold"]');
		expect(hold.text()).toContain("New requisitions are on hold while these requests remain unresolved.");
		expect(hold.text()).toContain("2");
		// Existing proceedings stay listed; nothing offers to restart them.
		expect(w.find('[data-testid="prg-proceeding"]').text()).toContain("REQ-MOH-2027-015");
		expect(w.text()).not.toContain("Resume");

		await w.find('[data-testid="prg-view-corrections"]').trigger("click");
		expect(w.emitted("view-corrections")[0][0]).toBe("PPI-MOH-2027-033");
	});
});

describe("ProgressScreen — no plan in force", () => {
	it("states it as a fact about the year, not as an error", () => {
		const w = make({ progress: { outcome: "NO_ACTIVE_PLAN" } });
		expect(w.find('[data-testid="prg-no-plan"]').text()).toContain("No plan is in force yet");
		expect(w.find('[data-testid="prg-context"]').exists()).toBe(false);
	});
});
