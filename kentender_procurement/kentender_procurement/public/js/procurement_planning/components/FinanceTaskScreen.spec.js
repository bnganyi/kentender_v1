// PLN-CHG-001 v1.12 §15 — FinanceTaskScreen component tests (D14).
// PLN-DES-10 exact fields (one task per Version), the over-approved variant
// that omits Confirm (§12.9), and §11.12's absences.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FinanceTaskScreen from "./FinanceTaskScreen.vue";

const LINE = {
	budget_line: "BL-1",
	budget_line_label: "MOH-BL-DHI-2027 — Digital health infrastructure programme",
	funding_source: "Government of Kenya",
	approved_display: "KES 100,000,000", planned_display: "KES 80,000,000",
	within_approved: true, within_approved_display: "Yes",
	reserved_display: "KES 0", committed_display: "KES 0", available_display: "KES 100,000,000",
	within_available: true, excess_display: "",
};

const WITHIN = {
	task: "FNT-1", task_reference: "FNT-MOH-2027-001", task_token: "tok",
	status: "Open", decided: false, can_decide: true, can_confirm: true,
	header: {
		eyebrow: "PLAN FUNDING CONFIRMATION", title: "Ministry of Health Annual Procurement Plan 2027/28",
		reference_line: "FNT-MOH-2027-001 · PLN-MOH-2027-001 · Version 1", badge: "Awaiting Finance",
	},
	summary: { plan_items: 1, value_display: "KES 80,000,000", lines_used: 1, reserved_share_display: "0% of plan value · target 30%" },
	as_at_display: "4 Dec 2026, 09:58 EAT",
	lines: [
		LINE,
		{ ...LINE, budget_line: "BL-2", budget_line_label: "MOH-BL-HWD-2027 — Digital health workforce development", approved_display: "KES 60,000,000", planned_display: "KES 0", available_display: "KES 60,000,000" },
	],
	within_approved: true,
	within_available: true,
	notice: { kind: "live", text: "The consolidated plan is within the approved budget on every Procurement Budget Line." },
	advisory: null,
	quiet_line: "Confirmation records that this plan fits the approved budget. It reserves no funds; reservation happens at requisition.",
	failing_lines: [],
};

function make(task = WITHIN) {
	return mount(FinanceTaskScreen, { props: { task, pending: false, errorSummary: "" } });
}

describe("FinanceTaskScreen — PLN-DES-10", () => {
	it("renders the header, the four-field plan summary and the eight-column affordability table", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("PLAN FUNDING CONFIRMATION");
		expect(w.find(".pln-quiet-ref").text()).toBe("FNT-MOH-2027-001 · PLN-MOH-2027-001 · Version 1");
		expect(w.find('[data-testid="fnt-badge"]').text()).toBe("Awaiting Finance");
		expect(w.find('[data-testid="fnt-summary"]').findAll("label").map((l) => l.text())).toEqual([
			"Plan Items", "Plan value", "Procurement Budget Lines used", "Reserved share",
		]);
		const card = w.find('[data-testid="fnt-affordability"]');
		expect(card.find(".kt-card-title").text()).toBe("Affordability");
		expect(w.find('[data-testid="fnt-as-at"]').text()).toBe("Position as at 4 Dec 2026, 09:58 EAT");
		expect(card.findAll("thead th").map((th) => th.text())).toEqual([
			"Procurement Budget Line", "Funding source", "Approved", "Planned in this Plan", "Within approved", "Reserved", "Committed", "Currently available",
		]);
		expect(card.findAll("tbody tr")).toHaveLength(2);
		expect(w.find('[data-testid="fnt-line-0"]').text()).toContain("Yes");
	});

	it("shows the green within-approved notice, the quiet no-reservation line and both decision controls", async () => {
		const w = make();
		const notice = w.find('[data-testid="fnt-within-approved"]');
		expect(notice.classes()).toContain("is-live");
		expect(notice.text()).toBe("The consolidated plan is within the approved budget on every Procurement Budget Line.");
		expect(w.find('[data-testid="fnt-quiet-line"]').text()).toContain("It reserves no funds; reservation happens at requisition.");
		expect(w.find('[data-testid="fnt-confirm"]').text()).toBe("Confirm plan funding");
		await w.find('[data-testid="fnt-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toHaveLength(1);
		await w.find('[data-testid="fnt-return"]').trigger("click");
		expect(w.emitted("open-return-dialog")).toHaveLength(1);
	});

	it("omits Confirm, names the excess and keeps Return when a line exceeds its approved amount", () => {
		const w = make({
			...WITHIN, can_confirm: false, within_approved: false,
			lines: [{ ...LINE, within_approved: false, within_approved_display: "No", planned_display: "KES 120,000,000", excess_display: "KES 20,000,000" }],
			notice: { kind: "critical", text: "The planned total exceeds the approved amount on one or more Procurement Budget Lines. Return the plan to the Planner." },
		});
		expect(w.find('[data-testid="fnt-over-approved"]').classes()).toContain("is-critical");
		expect(w.find('[data-testid="fnt-line-0"]').text()).toContain("exceeds by KES 20,000,000");
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-return"]').exists()).toBe(true);
	});

	it("shows the below-available advisory as quiet text that blocks nothing (§12.9)", () => {
		const w = make({ ...WITHIN, within_available: false, advisory: { kind: "advisory", text: "The planned total exceeds the currently available amount on at least one line. Planning and drawdown run on different horizons; this blocks nothing." } });
		expect(w.find('[data-testid="fnt-advisory"]').text()).toContain("this blocks nothing");
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(true);
	});

	it("removes the decision footer once decided or for a non-deciding reader", () => {
		expect(make({ ...WITHIN, status: "Completed", decided: true, can_decide: false, can_confirm: false, header: { ...WITHIN.header, badge: "Completed" } }).find(".pln-footer-bar").exists()).toBe(false);
		const reader = make({ ...WITHIN, can_decide: false, can_confirm: false });
		expect(reader.find('[data-testid="fnt-confirm"]').exists()).toBe(false);
		expect(reader.find('[data-testid="fnt-return"]').exists()).toBe(false);
	});

	it("carries no per-item list, editable amount, note, reservation or available-after column (§11.12)", () => {
		const w = make();
		expect(w.findAll("input, textarea, select")).toHaveLength(0);
		expect(w.text()).not.toContain("Available after confirmation");
		expect(w.text()).not.toContain("Note");
		expect(w.find('[data-testid="fnt-plan-item"]').exists()).toBe(false);
	});
});
