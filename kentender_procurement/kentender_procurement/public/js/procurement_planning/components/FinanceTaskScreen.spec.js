// PLN-CHG-001 v1.2 §15.1(5) — FinanceTaskScreen component tests (D9).
// PLN-DES-10 exact fields, the shortfall variant (§12.13/DES-16), and the
// decision footer's Confirm-omitted-on-shortfall rule (§12.9).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FinanceTaskScreen from "./FinanceTaskScreen.vue";

const SUFFICIENT = {
	task: "FNT-1", task_reference: "FNT-MOH-2027-021-001", task_token: "tok",
	status: "Open", decided: false, all_sufficient: true,
	header: {
		eyebrow: "FINANCE CONFIRMATION", title: "Confirm funding for Plan Item",
		reference_line: "FNT-MOH-2027-021-001 · PPI-MOH-2027-021", badge: "Awaiting Finance",
	},
	plan_item: {
		title: "National digital health infrastructure upgrade", department: "Digital Health",
		requirement_type: "Non-consulting services", value_display: "KES 80,000,000",
		procurement_method: "Open Tender", delivery_completion_display: "31 Aug 2027",
	},
	as_at_display: "4 Dec 2026, 09:58 EAT",
	lines: [
		{
			budget_line_label: "MOH-BL-DHI-2027 — Digital health infrastructure programme",
			funding_source: "Government of Kenya",
			approved_display: "KES 100,000,000", reserved_display: "KES 0",
			committed_display: "KES 0", available_display: "KES 100,000,000",
			required_display: "KES 80,000,000", available_after_display: "KES 20,000,000",
			sufficient: true,
		},
	],
};

function make(task = SUFFICIENT) {
	return mount(FinanceTaskScreen, { props: { task, pending: false, errorSummary: "" } });
}

describe("FinanceTaskScreen — PLN-DES-10", () => {
	it("renders the exact Plan Item card and funding position table", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("FINANCE CONFIRMATION");
		expect(w.find('[data-testid="fnt-plan-item"]').text()).toContain(
			"National digital health infrastructure upgrade"
		);
		expect(w.find('[data-testid="fnt-position"]').text()).toContain("KES 100,000,000");
		expect(w.text()).toContain("Position as at 4 Dec 2026, 09:58 EAT");
	});

	it("shows the sufficient notice and both decision controls", async () => {
		const w = make();
		expect(w.find('[data-testid="fnt-sufficient"]').exists()).toBe(true);
		expect(w.find('[data-testid="fnt-shortfall"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(true);
		await w.find('[data-testid="fnt-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toHaveLength(1);
		await w.find('[data-testid="fnt-return"]').trigger("click");
		expect(w.emitted("open-return-dialog")).toHaveLength(1);
	});

	it("omits Confirm and shows the shortfall notice when funding is insufficient", () => {
		const shortfall = {
			...SUFFICIENT, all_sufficient: false,
			lines: [{ ...SUFFICIENT.lines[0], sufficient: false, available_after_display: "KES 0" }],
		};
		const w = make(shortfall);
		expect(w.find('[data-testid="fnt-shortfall"]').text()).toContain("Funding is insufficient");
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-return"]').exists()).toBe(true);
	});

	it("removes the decision footer once the task is decided", () => {
		const w = make({ ...SUFFICIENT, status: "Completed" });
		expect(w.find('[data-testid="fnt-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="fnt-return"]').exists()).toBe(false);
	});

	it("carries no editable amount, Budget Line change, optional note or partial-confirmation control (§11.12)", () => {
		const w = make();
		expect(w.findAll("input, textarea, select")).toHaveLength(0);
		expect(w.text()).not.toContain("Note");
		expect(w.text()).not.toContain("Partial");
	});
});
