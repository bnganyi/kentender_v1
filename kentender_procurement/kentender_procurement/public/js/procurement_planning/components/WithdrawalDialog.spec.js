// PLN-CHG-001 v1.23 §10.12 — WithdrawalDialog component tests
// (U13-WITHDRAWAL-REQUEST-DIALOG / U13-WITHDRAWAL-DECISION-DIALOG).
//
// Two people, two dialogs. The one who asks writes the reason; the one who
// decides reads it and cannot rewrite it.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WithdrawalDialog from "./WithdrawalDialog.vue";

const REASON = "The approved plan states the wrong delivery boundary for the infrastructure package.";

function task(overrides = {}) {
	return {
		plan_title: "Ministry of Health Annual Procurement Plan 2027/28",
		plan_reference: "PLN-MOH-2027-001",
		version: { number: 1, reference: "PLN-MOH-2027-001-V1" },
		publication_confirmation: "Confirmed not published",
		withdrawal_request: null,
		...overrides,
	};
}

const make = (props = {}) =>
	mount(WithdrawalDialog, { props: { task: task(), mode: "request", pending: false, error: "", ...props } });

describe("WithdrawalDialog — U13-WITHDRAWAL-REQUEST-DIALOG", () => {
	it("names the plan and states that its content is confirmed not published", () => {
		const w = make();
		expect(w.find('[data-testid="pub-withdrawal-title"]').text()).toBe("Request withdrawal for correction");
		expect(w.find('[data-testid="pub-withdrawal-plan"]').text()).toContain("PLN-MOH-2027-001");
		expect(w.find('[data-testid="pub-withdrawal-confirmation"]').text()).toBe("Confirmed not published");
	});

	it("says what will and will not happen, before the action", () => {
		const text = make().find('[data-testid="pub-withdrawal-consequence"]').text();
		expect(text).toContain("The approved plan will remain in history.");
		expect(text).toContain("If the request is approved, a correction draft will repeat the required review and approval.");
	});

	it("will not send a request without a reason someone can act on", async () => {
		const w = make();
		expect(w.find('[data-testid="pub-withdrawal-confirm"]').attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pub-withdrawal-reason"]').setValue("too short");
		expect(w.find('[data-testid="pub-withdrawal-confirm"]').attributes("disabled")).toBeDefined();

		await w.find('[data-testid="pub-withdrawal-reason"]').setValue(REASON);
		expect(w.find('[data-testid="pub-withdrawal-confirm"]').attributes("disabled")).toBeUndefined();
		await w.find('[data-testid="pub-withdrawal-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toBe(REASON);
	});
});

describe("WithdrawalDialog — U13-WITHDRAWAL-DECISION-DIALOG", () => {
	const decision = () =>
		make({
			mode: "decision",
			task: task({
				withdrawal_request: {
					reason: REASON,
					requested_by_name: "Amina Hassan",
					requested_display: "11 Dec 2026, 09:00 EAT",
					capacity: "Cabinet Secretary",
				},
			}),
		});

	it("shows the request it is deciding on, and who made it", () => {
		const w = decision();
		expect(w.find('[data-testid="pub-withdrawal-title"]').text()).toBe("Withdraw this plan for correction?");
		const request = w.find('[data-testid="pub-withdrawal-request"]').text();
		expect(request).toContain(REASON);
		expect(request).toContain("Amina Hassan");
		expect(request).toContain("11 Dec 2026, 09:00 EAT");
	});

	it("cannot rewrite the reason it is deciding on", () => {
		const w = decision();
		expect(w.find('[data-testid="pub-withdrawal-reason"]').exists()).toBe(false);
		expect(w.findAll("textarea")).toHaveLength(0);
	});

	it("offers exactly one business action and no return", () => {
		const w = decision();
		expect(w.find('[data-testid="pub-withdrawal-confirm"]').text()).toBe("Withdraw for correction");
		expect(w.find('[data-testid="pub-withdrawal-confirm"]').attributes("disabled")).toBeUndefined();
		expect(w.text()).not.toContain("Return");
	});

	it("states the consequence in the decided form", () => {
		expect(decision().find('[data-testid="pub-withdrawal-consequence"]').text()).toContain(
			"A correction draft will be prepared and will repeat the required review and approval.",
		);
	});
});
