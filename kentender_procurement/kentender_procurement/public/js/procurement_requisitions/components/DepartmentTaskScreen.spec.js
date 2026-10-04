import { describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import DepartmentTaskScreen from "./DepartmentTaskScreen.vue";
import { context, departmentTask } from "./fixtures.js";

// The command runner as the root builds it: a failure lands in commandError.
function failingContext(error, afterReload) {
	const setup = context();
	setup.ctx.run = async (label, fn) => {
		try {
			return await fn("key");
		} catch (e) {
			setup.ctx.commandError.value = { label, ...error };
			return null;
		}
	};
	setup.ctx.clearError = () => {
		setup.ctx.commandError.value = null;
	};
	setup.ctx.reload = vi.fn(async () => afterReload && afterReload());
	return setup;
}

describe("DepartmentTaskScreen (REQ-DES-07)", () => {
	it("the lead HoD sees the question, the certification and the three decisions", () => {
		const { global } = context();
		const w = mount(DepartmentTaskScreen, { props: { view: departmentTask() }, global });
		expect(w.find('[data-testid="req-question"]').text()).toContain("both departments’ need");
		expect(w.text()).toContain("I confirm that this requisition states");
		expect(w.find('[data-testid="req-submit"]').text()).toBe("Submit to Procurement");
		expect(w.find('[data-testid="req-return"]').exists()).toBe(true);
		expect(w.find('[data-testid="req-action-planning"]').exists()).toBe(true);
	});

	it("SUBMITTED: read-only, no decision, only the two quiet actions remain", () => {
		const { global } = context();
		const w = mount(DepartmentTaskScreen, { props: { view: departmentTask("SUBMITTED") }, global });
		expect(w.find('[data-testid="req-submit"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-return"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-question"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-other-actions"]').exists()).toBe(true);
	});

	it("an unanswered submit re-reads the record and reports it committed — no second decision offered", async () => {
		const view = departmentTask();
		const { global, ctx } = failingContext({ code: "", httpStatus: 0, message: "network" });
		ctx.api.submitToProcurement = vi.fn().mockRejectedValue(new Error("network"));
		const w = mount(DepartmentTaskScreen, { props: { view }, global });
		ctx.reload = vi.fn(async () => {
			await w.setProps({ view: { ...view, task: { ...view.task, status: "Completed" } } });
		});
		await w.find('[data-testid="req-submit"]').trigger("click");
		await flushPromises();
		expect(ctx.reload).toHaveBeenCalled();
		expect(w.find('[data-testid="req-uncertain-committed"]').text()).toBe("Requisition submitted to Procurement");
		expect(w.find('[data-testid="req-submit"]').exists()).toBe(false);
	});

	it("an unanswered submit that did not commit states the retry-safe message", async () => {
		const { global, ctx } = failingContext({ code: "", httpStatus: 502, message: "Bad gateway" });
		ctx.api.submitToProcurement = vi.fn().mockRejectedValue(new Error("bad gateway"));
		const w = mount(DepartmentTaskScreen, { props: { view: departmentTask() }, global });
		await w.find('[data-testid="req-submit"]').trigger("click");
		await flushPromises();
		expect(w.find('[data-testid="req-uncertain-unconfirmed"]').text()).toBe("The result could not be confirmed. Check the current requisition before trying again.");
	});

	it("a stated refusal is shown as that refusal, not as uncertainty", async () => {
		const { global, ctx } = failingContext({ code: "REQ_SOD_BLOCKED", httpStatus: 417, message: "You may not complete this decision on this Version." });
		ctx.api.submitToProcurement = vi.fn().mockRejectedValue(new Error("refused"));
		const w = mount(DepartmentTaskScreen, { props: { view: departmentTask() }, global });
		await w.find('[data-testid="req-submit"]').trigger("click");
		await flushPromises();
		expect(ctx.reload).not.toHaveBeenCalled();
		expect(w.find('[data-testid="req-decision-error"]').text()).toBe("You may not complete this decision on this Version.");
	});
});
