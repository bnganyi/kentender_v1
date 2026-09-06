// PLN-CHG-001 v1.12 §15 — ShiftScheduleDialog component tests (D14).
// PLN-DES-14A: server-computed proposal rows, every row pre-included and
// independently uncheckable, one shared 20–500 character reason, no baseline
// or actual-date control (§12.12, PLN-AC-125..127).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ShiftScheduleDialog from "./ShiftScheduleDialog.vue";

const ROWS = [
	{ milestone: "bid_opening", label: "Bid opening", current_forecast: "2027-05-22", proposed_forecast: "2027-06-05", included: true, is_anchor: true },
	{ milestone: "evaluation_completion", label: "Evaluation completion", current_forecast: "2027-06-21", proposed_forecast: "2027-07-05", included: true, is_anchor: false },
	{ milestone: "award_approval", label: "Tender award approval", current_forecast: "2027-06-26", proposed_forecast: "2027-07-10", included: true, is_anchor: false },
	{ milestone: "award_notification", label: "Notification of award", current_forecast: "2027-06-28", proposed_forecast: "2027-07-12", included: true, is_anchor: false },
	{ milestone: "contract_signing", label: "Contract signing", current_forecast: "2027-07-12", proposed_forecast: "2027-07-26", included: true, is_anchor: false },
	{ milestone: "delivery_completion", label: "Delivery or implementation completion", current_forecast: "2027-08-31", proposed_forecast: "2027-09-14", included: true, is_anchor: false },
];

const REASON = "Tender Preparation confirmed the issue date will slip two weeks pending template release.";

function make(props = {}) {
	return mount(ShiftScheduleDialog, {
		props: { milestoneLabel: "Bid opening", newDate: "2027-06-05", rows: ROWS, pending: false, error: "", ...props },
	});
}

describe("ShiftScheduleDialog — PLN-DES-14A", () => {
	it("renders the exact title, context line, date field and the proposed-shift table", () => {
		const w = make();
		expect(w.find(".kt-dialog-title").text()).toBe("Shift schedule from here — Bid opening");
		expect(w.find(".pln-dialog-context").text()).toContain("Changing Bid opening recalculates every later milestone by the same number of days.");
		expect(w.find('label[for="pln-shift-date"]').text()).toBe("New forecast date for Bid opening");
		expect(w.find('[data-testid="pln-shift-date"]').element.value).toBe("2027-06-05");
		expect(w.findAll("thead th").map((th) => th.text())).toEqual(["", "Milestone", "Current forecast", "Proposed forecast"]);
		const rows = w.findAll("tbody tr");
		expect(rows).toHaveLength(6);
		expect(rows[0].text()).toContain("22 May 2027");
		expect(rows[0].text()).toContain("5 Jun 2027");
		expect(rows.every((r) => r.find("input[type=checkbox]").element.checked)).toBe(true);
		// the proposed forecast is never independently editable
		expect(w.findAll("tbody input[type=date], tbody input[type=text]")).toHaveLength(0);
	});

	it("emits date-change so the server recomputes the proposal (PLN-AC-124)", async () => {
		const w = make();
		await w.find('[data-testid="pln-shift-date"]').setValue("2027-06-08");
		expect(w.emitted("date-change")[0][0]).toBe("2027-06-08");
	});

	it("requires a 20–500 character reason and confirms with the included rows only", async () => {
		const w = make();
		const confirm = w.find('[data-testid="pln-shift-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pln-shift-reason"]').setValue("too short");
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pln-shift-reason"]').setValue(REASON);
		expect(confirm.attributes("disabled")).toBeUndefined();
		await w.find('[data-testid="pln-shift-include-delivery_completion"]').setValue(false);
		await w.find('[data-testid="pln-shift-include-contract_signing"]').setValue(false);
		await confirm.trigger("click");
		const [payload] = w.emitted("confirm")[0];
		expect(payload.included_milestones).toEqual(["bid_opening", "evaluation_completion", "award_approval", "award_notification"]);
		expect(payload.reason).toBe(REASON);
	});

	it("keeps the revised milestone itself always included", () => {
		const w = make();
		expect(w.find('[data-testid="pln-shift-include-bid_opening"]').attributes("disabled")).toBeDefined();
	});

	it("carries no baseline field, per-row reason or actual-date control (§11.16A)", () => {
		const w = make();
		expect(w.text()).not.toContain("Baseline");
		expect(w.text()).not.toContain("Actual");
		expect(w.findAll("textarea")).toHaveLength(1);
		expect(w.findAll("button").map((b) => b.text())).toEqual(["Cancel", "Confirm shift"]);
	});
});
