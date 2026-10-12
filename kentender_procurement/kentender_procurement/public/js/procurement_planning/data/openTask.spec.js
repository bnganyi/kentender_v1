import { describe, expect, it } from "vitest";

import { directTaskRoute } from "./openTask.js";

const AO_TASK = { label: "Review and adopt the plan", route: ["procurement-planning", "review", "AOT-1"], opens_directly: true };
const FINANCE_TASK = { label: "Review and confirm funding", route: ["procurement-planning", "finance", "FIN-1"] };

describe("directTaskRoute", () => {
	it("sends the holder of a decision task from the plan to the task itself", () => {
		expect(directTaskRoute("plan", { open_task: AO_TASK })).toEqual(AO_TASK.route);
	});

	it("leaves a task that is only offered, not opened for them, as a button", () => {
		expect(directTaskRoute("plan", { open_task: FINANCE_TASK })).toBeNull();
	});

	it("does nothing without a task, or on any page but the plan itself", () => {
		expect(directTaskRoute("plan", { open_task: null })).toBeNull();
		expect(directTaskRoute("plan", null)).toBeNull();
		expect(directTaskRoute("progress", { open_task: AO_TASK })).toBeNull();
		expect(directTaskRoute("governance", { open_task: AO_TASK })).toBeNull();
	});
});
