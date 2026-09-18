// PLN-CHG-001 v1.23 §10.9 — FinanceTaskScreen component tests (U10).
//
// The distinction this screen exists to protect: an approved-amount excess
// blocks confirmation, low current availability does not. Both must be
// visible, and they must not look alike.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FinanceTaskScreen from "./FinanceTaskScreen.vue";

function line(overrides = {}) {
	return {
		budget_line: "bl-dhi",
		budget_line_reference: "MOH-BL-DHI-2027",
		line_name: "Digital health infrastructure programme",
		funding_source: "Government of Kenya",
		approved_display: "KES 100,000,000",
		planned_display: "KES 80,000,000",
		difference_display: "KES 20,000,000",
		result: "Within budget",
		result_kind: "live",
		within_approved: true,
		within_available: true,
		reserved_display: "KES 0",
		committed_display: "KES 0",
		available_display: "KES 100,000,000",
		excess_display: "",
		...overrides,
	};
}

function task(overrides = {}) {
	return {
		outcome: "OK",
		task: "FNT-MOH-2027-001",
		status: "Open",
		can_decide: true,
		can_confirm: true,
		segregated: false,
		is_reassessment: false,
		stale: false,
		header: {
			title: "Ministry of Health Annual Procurement Plan 2027/28",
			reference_line: "FNT-MOH-2027-001 · PLN-MOH-2027-001 · Version 1",
		},
		budget_reference: "MOH-BUD-2027-001",
		as_at_display: "3 Dec 2026, 09:00 EAT",
		lines: [line(), line({ budget_line: "bl-hwd", budget_line_reference: "MOH-BL-HWD-2027", line_name: "Digital health workforce development", approved_display: "KES 60,000,000", planned_display: "KES 50,000,000", difference_display: "KES 10,000,000", available_display: "KES 60,000,000" })],
		history: [],
		...overrides,
	};
}

function make(props = {}) {
	return mount(FinanceTaskScreen, { props: { task: task(), pending: false, errorSummary: "", ...props } });
}

describe("FinanceTaskScreen — U10 BASE", () => {
	it("asks the one question it exists to answer", () => {
		const w = make();
		expect(w.find('[data-testid="fnt-title"]').text()).toBe("Check funding for the annual plan");
		expect(w.text()).toContain("Confirm whether each planned amount is within its approved budget line.");
		expect(w.find('[data-testid="fnt-badge"]').text()).toBe("Your decision required");
	});

	it("puts approved, planned, difference and result in the first view", () => {
		const w = make();
		const headers = w.findAll('[data-testid="fnt-comparison"] th').map((th) => th.text());
		expect(headers).toEqual([
			"Budget line", "Line name", "Approved amount", "Planned amount", "Difference", "Result", "Action",
		]);
		expect(w.find('[data-testid="fnt-line-0"]').text()).toContain("KES 20,000,000");
		expect(w.find('[data-testid="fnt-line-0"]').text()).toContain("Within budget");
	});

	it("keeps current balances collapsed and advisory", () => {
		const w = make();
		const balances = w.find('[data-testid="fnt-balances"]');
		expect(balances.attributes("open")).toBeUndefined();
		expect(balances.text()).toContain("advisory and do not affect the affordability decision");
	});

	it("says what confirming does and does not do", () => {
		const w = make();
		expect(w.find('[data-testid="fnt-consequence"]').text()).toBe(
			"Confirming records affordability. It does not reserve funds or approve the plan.",
		);
	});

	it("offers both decisions when the plan is within budget", () => {
		const w = make();
		expect(w.find('[data-testid="fnt-confirm"]').text()).toBe("Confirm plan funding");
		expect(w.find('[data-testid="fnt-return"]').attributes("disabled")).toBeUndefined();
	});
});

describe("FinanceTaskScreen — availability versus affordability", () => {
	it("U10-LOW-AVAILABILITY: says the confirmation is still permitted", () => {
		const w = make({
			task: task({ lines: [line({ within_available: false, available_display: "KES 10,000,000" })] }),
		});
		expect(w.find('[data-testid="fnt-low-availability-0"]').text()).toContain(
			"The plan is still within the approved budget, so funding confirmation is permitted.",
		);
		// Both decisions remain available.
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(true);
		expect(w.find('[data-testid="fnt-return"]').attributes("disabled")).toBeUndefined();
	});

	it("U10-OVER-APPROVED: removes Confirm, keeps Return, and names the exact excess", () => {
		const w = make({
			task: task({
				can_confirm: false,
				lines: [
					line({
						approved_display: "KES 70,000,000",
						planned_display: "KES 80,000,000",
						difference_display: "KES -10,000,000",
						result: "Exceeds approved amount",
						result_kind: "critical",
						within_approved: false,
						excess_display: "KES 10,000,000",
					}),
				],
			}),
		});
		expect(w.find('[data-testid="fnt-excess-0"]').text()).toContain(
			"exceeds its approved budget by KES 10,000,000",
		);
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-return"]').attributes("disabled")).toBeUndefined();
	});
});

describe("FinanceTaskScreen — other states", () => {
	it("U10-REASSESS: retitles and says it is evidence, not re-approval", () => {
		const w = make({ task: task({ is_reassessment: true }) });
		expect(w.find('[data-testid="fnt-title"]').text()).toBe("Check funding again for the current plan");
		expect(w.find('[data-testid="fnt-reassessment-notice"]').text()).toContain(
			"does not change or re-approve the plan",
		);
	});

	it("U10-CHANGED: says the amounts moved and offers the replacement when there is one", () => {
		const w = make({ task: task({ stale: true, replacement_route: ["procurement-planning", "finance", "FNT-2"] }) });
		expect(w.find('[data-testid="fnt-changed"]').text()).toContain("The amounts for this review have changed.");
		expect(w.find('[data-testid="fnt-open-replacement"]').text()).toBe("Open updated funding review");
	});

	it("U10-CHANGED: names the responsible role when there is no replacement to open", () => {
		const w = make({ task: task({ stale: true }) });
		expect(w.find('[data-testid="fnt-open-replacement"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-changed"]').text()).toContain("Responsible role: Procurement Planner");
	});

	it("blocks a segregated actor from both decisions", () => {
		const w = make({ task: task({ segregated: true, can_decide: false, can_confirm: false }) });
		expect(w.find('[data-testid="fnt-segregated"]').text()).toContain("independent decision-maker is required");
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(false);
		// §6.1 — absent, not disabled: a greyed control tells the reader
		// nothing about why the decision is not theirs. The notice does.
		expect(w.find('[data-testid="fnt-return"]').exists()).toBe(false);
	});

	it("shows no decision area once the review is decided", () => {
		const w = make({ task: task({ status: "Completed", can_decide: false, can_confirm: false }) });
		expect(w.find('[data-testid="fnt-footer"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-comparison"]').exists()).toBe(true);
	});
});
