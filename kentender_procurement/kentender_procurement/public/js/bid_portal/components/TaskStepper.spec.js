// A task page says which step of the bid it is: the five tasks in their fixed
// order with their states, the current one marked, and Previous / Next links to
// its neighbours. Navigation only: the server decides what each state is.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import TaskStepper from "./TaskStepper.vue";

const BASE = "/tenders/TND-1/bid";
const STEP = {
	number: 3, of: 5, label: "Requirements and supporting evidence",
	previous: { label: "Company and declarations", href: `${BASE}/company` },
	next: { label: "Price", href: `${BASE}/price` },
	tasks: [
		{ number: 1, key: "documents", label: "Tender documents", short: "Tender documents", status: "Complete", tone: "live", href: `${BASE}/documents`, current: false },
		{ number: 2, key: "company", label: "Company", short: "Company and declarations", status: "In progress", tone: "pending", href: `${BASE}/company`, current: false },
		{ number: 3, key: "requirements", label: "Requirements", short: "Requirements", status: "Complete", tone: "live", href: `${BASE}/requirements`, current: true },
		{ number: 4, key: "price", label: "Price", short: "Price", status: "Complete", tone: "live", href: `${BASE}/price`, current: false },
		{ number: 5, key: "review", label: "Review and submit", short: "Review and submit", status: "Not started", tone: "draft", href: `${BASE}/review`, current: false },
	],
};
const render = (step) => mount(TaskStepper, { props: { step }, global: { config: { globalProperties: { __: (s, args = []) => s.replace(/\{(\d+)\}/g, (_, i) => args[i]) } } } });

describe("TaskStepper", () => {
	it("lists the five tasks in order, numbered, with the current one marked", () => {
		const wrapper = render(STEP);
		const items = wrapper.findAll(".bds-stepper-item");
		expect(items.map((a) => a.get(".bds-stepper-number").text())).toEqual(["1", "2", "3", "4", "5"]);
		expect(items.map((a) => a.get(".bds-stepper-name").text())).toEqual(["Tender documents", "Company and declarations", "Requirements", "Price", "Review and submit"]);
		expect(items.map((a) => a.attributes("aria-current") || null)).toEqual([null, null, "step", null, null]);
		expect(items.map((a) => a.attributes("href"))).toEqual(Object.values(STEP.tasks).map((t) => t.href));
		expect(items[1].classes()).toContain("is-pending");
		expect(items[1].attributes("aria-label")).toBe("Step 2: Company and declarations, In progress");
	});

	it("says why Review is not ready when it is not, and shows each state otherwise", () => {
		const blocked = { ...STEP, tasks: STEP.tasks.map((t) => (t.key === "review" ? { ...t, hint: "Not ready: finish the other tasks first" } : t)) };
		const items = render(blocked).findAll(".bds-stepper-item");
		expect(items[4].attributes("title")).toBe("Not ready: finish the other tasks first");
		expect(items[4].attributes("aria-label")).toBe("Step 5: Review and submit, Not ready: finish the other tasks first");
		expect(items[1].attributes("title")).toBe("In progress"); // no hint: the state
	});

	it("says which step it is and links to the neighbouring tasks", () => {
		const wrapper = render(STEP);
		expect(wrapper.get('[data-testid="bds-stepper-where"]').text()).toBe("Step 3 of 5");
		expect(wrapper.get('[data-testid="bds-stepper-previous"]').text()).toBe("← Company and declarations");
		expect(wrapper.get('[data-testid="bds-stepper-previous"]').attributes("href")).toBe(`${BASE}/company`);
		expect(wrapper.get('[data-testid="bds-stepper-next"]').text()).toBe("Price →");
	});

	it("has no Previous on the first task and no Next on the last", () => {
		const first = render({ ...STEP, number: 1, previous: null });
		expect(first.find('[data-testid="bds-stepper-previous"]').exists()).toBe(false);
		expect(first.find('[data-testid="bds-stepper-next"]').exists()).toBe(true);
		const last = render({ ...STEP, number: 5, next: null });
		expect(last.find('[data-testid="bds-stepper-next"]').exists()).toBe(false);
	});
});
