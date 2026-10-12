// REQ-CHG-001 v1.17 §13.4A–B — the three tasks read as numbered steps, and Review and
// submit says what needs attention once, in the same panel as the other tasks.
import { beforeEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import ProgressRow from "./shared/ProgressRow.vue";
import ReviewTask from "./ReviewTask.vue";
import { context, editor, review } from "./fixtures.js";

beforeEach(() => window.sessionStorage.clear());

describe("ProgressRow — numbered steps", () => {
	it("draws three numbered steps, says each state in words and marks the one being looked at", async () => {
		const tasks = editor("COMPLETE").tasks;
		const w = mount(ProgressRow, { props: { tasks, selected: "request_details" } });
		const steps = w.findAll("li.kt-journey-stage");
		expect(steps).toHaveLength(3);
		expect(w.find("ol").classes()).toContain("kt-journey");
		expect(steps.map((s) => s.find(".kt-journey-title").text())).toEqual(["Request details", "Requirements", "Review and submit"].map((t, i) => (i === 0 ? t : `${i + 1}${t}`)));
		// the first is complete (a check, not a number); the second needs attention
		expect(steps[0].classes()).toContain("is-done");
		expect(steps[0].find(".kt-journey-check").exists()).toBe(true);
		expect(steps[1].classes()).toContain("is-blocked");
		expect(steps[0].attributes("aria-current")).toBe("step");
		expect(steps[1].attributes("aria-current")).toBeUndefined();
		expect(steps[0].find('[data-testid="req-step-state"]').text()).toBe("You are here · Complete");
		expect(steps[1].find('[data-testid="req-step-state"]').text()).toBe("Needs attention");
		// not a tab list: a requester may go to any step, and each is a plain button
		expect(w.find('[role="tablist"]').exists()).toBe(false);
		await w.find('[data-testid="req-task-review_submit"]').trigger("click");
		expect(w.emitted("select")[0]).toEqual(["review_submit"]);
	});
});

describe("ReviewTask — one attention panel", () => {
	it("lists every blocking finding once, links each to the task that fixes it, and has no pink strips", async () => {
		const { global } = context();
		const view = review();
		view.review = { ...view.review, result: "" };
		view.findings = [
			{ code: "RESTRICTIVE_TERM", severity: "Blocking", task: "request_details", message: "“Dell” in the item “Laptops” is a brand or restrictive term." },
			{ code: "X", severity: "Blocking", task: "requirements", message: "Review the standard requirements." },
		];
		const w = mount(ReviewTask, { props: { view }, global });
		expect(w.find('[data-testid="req-attention-head"]').text()).toBe("2 things need attention");
		expect(w.findAll('[data-testid="req-attention-item"]')).toHaveLength(2 + 1); // two blocking + the date advisory
		expect(w.find(".kt-notice.is-critical").exists()).toBe(false);
		expect(w.findAll('[data-testid="req-footer-status"]')).toHaveLength(1);
		await w.findAll(".req-attention-link")[1].trigger("click");
		expect(w.emitted("select")[0]).toEqual(["requirements"]);
	});

	it("shows the date note as an advisory beside the ready result, not as an error", () => {
		const { global } = context();
		const w = mount(ReviewTask, { props: { view: review() }, global });
		expect(w.find('[data-testid="req-review-result"]').exists()).toBe(true);
		expect(w.find('[data-testid="req-attention-head"]').text()).toBe("For your attention");
		expect(w.find(".req-attention-tag").text()).toBe("Note");
		expect(w.find('[data-testid="req-footer-status"]').exists()).toBe(false);
	});
});
