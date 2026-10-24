// REQ-CHG-001 v1.20 §13.15 — the 'Unused allowance and funding' section on the authorised requisition, in each of the three states.
// The section is the server's own (permitted rows only); the screen restores and releases nothing, and the only action it can offer is the
// ordinary route to a fresh requisition, and only when the server sent one.
import { beforeEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import AuthorisedScreen from "./AuthorisedScreen.vue";
import { authorised, context } from "./fixtures.js";

beforeEach(() => window.sessionStorage.clear());

function section(status, extra = {}) {
	const copy = {
		Pending: ["Restoring unused allowance and funding", "The allowance and funding of this requisition are being restored after the tender was cancelled. A new requisition for the same purchase can be authorised when restoration is complete."],
		Completed: ["Unused allowance and funding restored", "This requisition stays authorised and its handoff stays used. The unused allowance and funding were restored after the tender was cancelled."],
		"Needs attention": ["Unused allowance and funding need attention", "The unused allowance and funding could not be restored automatically. Nothing was changed."],
	}[status];
	return {
		title: "Unused allowance and funding", status, label: copy[0], explanation: copy[1], reason: status === "Needs attention" ? "Planning — The originating drawdown was already reversed for another reason." : "",
		rows: [{ key: "DL-1", source: "Ministry of Health Headquarters", quantity: "60 Each", value: "KES 6,000,000.00", restored: "60 Each · KES 6,000,000.00", released: "KES 6,000,000.00" }],
		partial_view: false, technical: [{ label: "Recovery", value: "CRR-00001" }], next_step: null, ...extra,
	};
}

function mountWith(recovery) {
	const { global } = context();
	const view = { ...authorised("BASE"), cancellation_recovery: recovery };
	return mount(AuthorisedScreen, { props: { view }, global });
}

describe("AuthorisedScreen — unused allowance and funding", () => {
	it("Pending: the label and explanation, no restored columns, no button", () => {
		const w = mountWith(section("Pending"));
		expect(w.find('[data-testid="req-resource-recovery-label"]').text()).toBe("Restoring unused allowance and funding");
		expect(w.find('[data-testid="req-resource-recovery-explanation"]').text()).toContain("A new requisition for the same purchase can be authorised when restoration is complete");
		expect(w.find('[data-testid="req-resource-recovery-rows"] thead').text()).not.toContain("restored");
		expect(w.find('[data-testid="req-resource-recovery-next"]').exists()).toBe(false);
	});
	it("Completed: the exact amounts, and the start button only when the server gave a route", async () => {
		const withoutRoute = mountWith(section("Completed"));
		expect(withoutRoute.find('[data-testid="req-resource-recovery-rows"] tbody').text()).toContain("60 Each · KES 6,000,000.00");
		expect(withoutRoute.find('[data-testid="req-resource-recovery-next"]').exists()).toBe(false);
		const withRoute = mountWith(section("Completed", { next_step: { label: "Start a new requisition for this purchase", route: "/app/procurement-requisitions/new/PPI-1" } }));
		expect(withRoute.find('[data-testid="req-resource-recovery-next"]').text()).toBe("Start a new requisition for this purchase");
	});
	it("Needs attention: the owner's real reason, and a department-scoped reader is told the rows are partial", () => {
		const w = mountWith(section("Needs attention", { partial_view: true }));
		expect(w.find('[data-testid="req-resource-recovery-reason"]').text()).toContain("already reversed for another reason");
		expect(w.find('[data-testid="req-resource-recovery"]').text()).toContain("Only the sources of your department are shown.");
	});
	it("nothing is drawn when there is no section", () => {
		const w = mountWith(null);
		expect(w.find('[data-testid="req-resource-recovery"]').exists()).toBe(false);
	});
});
