// BDS-CHG-001 v0.8 §10.12 behaviour of Review bid: the read decides the one
// header action (Submit bid only for the signatory on a Ready bid), the
// computed result, each task's Review link and exact issue links; a guidance
// fix that names a task opens it; the narrow frame lists the tasks as cards.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import ReviewTaskScreen from "./ReviewTaskScreen.vue";
import { reviewTask } from "./review.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor(call = vi.fn(async () => reviewTask())) {
	const route = ref({ path: `/tenders/${REF}/bid/review`, segments: ["tenders", REF, "bid", "review"], query: {} });
	const go = vi.fn();
	return { call, go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal = portalFor()) {
	return mount(ReviewTaskScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Review bid", () => {
	it("offers Submit bid to the signatory on a ready bid, with the computed result", () => {
		const wrapper = mountWith(reviewTask());
		expect(wrapper.get('[data-testid="bds-review-action"]').text()).toBe("Submit bid");
		expect(wrapper.get('[data-testid="bds-review-action"]').attributes("href")).toBe(`/tenders/${REF}/bid/submit`);
		expect(wrapper.get('[data-testid="bds-review-submit"]').text()).toBe("Submit bid");
		expect(wrapper.get('[data-testid="bds-review-result"]').text()).toBe("All required bid information is complete.");
		expect(wrapper.get('[data-testid="bds-review-security"]').text()).toContain("recorded as received");
		const links = wrapper.findAll('[data-testid="bds-review-tasks"] tbody td:last-child a').map((a) => a.attributes("href"));
		expect(links).toEqual(["documents", "company", "requirements", "price"].map((k) => `/tenders/${REF}/bid/${k}`));
		expect(wrapper.get('[data-testid="bds-review-task-review"]').text()).toContain("—");
	});

	it("shows the representative the same review with no Submit anywhere", () => {
		const wrapper = mountWith(reviewTask("REPRESENTATIVE"));
		expect(wrapper.find('[data-testid="bds-review-action"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="bds-review-submit"]').exists()).toBe(false);
		expect(wrapper.text()).not.toContain("Submit bid");
		expect(wrapper.get('[data-testid="bds-review-result"]').exists()).toBe(true);
	});

	it("links a rejected file at its task, and Fix item opens that task", async () => {
		const portal = portalFor();
		const wrapper = mountWith(reviewTask("EVIDENCE"), portal);
		expect(wrapper.find('[data-testid="bds-review-result"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="bds-review-submit"]').exists()).toBe(false);
		const issue = wrapper.get('[data-testid="bds-review-task-requirements"] .bds-issue-link a');
		expect([issue.text(), issue.attributes("href")]).toEqual(["Replace the rejected product datasheet", `/tenders/${REF}/bid/requirements?item=g-datasheet`]);
		await wrapper.findAll("button").find((b) => b.text() === "Fix item").trigger("click");
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/requirements`);
	});

	it("keeps preparation open while portal information is restored", () => {
		const wrapper = mountWith(reviewTask("CFG-PREP"));
		const action = wrapper.get('[data-testid="bds-review-action"]');
		expect([action.text(), action.classes()]).toEqual(["Continue saved bid", expect.arrayContaining(["btn-primary"])]);
		expect(wrapper.get('[data-testid="bds-review-availability"]').text()).toContain("Submission is unavailable");
		expect(wrapper.find('[data-testid="bds-review-result"]').exists()).toBe(false);
	});

	it("reads the review when it opens without a first payload", async () => {
		const call = vi.fn(async () => reviewTask());
		const wrapper = mountWith(null, portalFor(call));
		await flushPromises();
		expect(call.mock.calls[0][1]).toMatchObject({ tender_reference: REF, task: "review" });
		expect(wrapper.get('[data-testid="bds-review-summary"]').text()).toContain("KES 46,400,000.00");
	});

	it("lists the tasks as labelled cards on a narrow screen", () => {
		globalThis.__narrow = true;
		const wrapper = mountWith(reviewTask("ADDENDUM"));
		expect(wrapper.find('[data-testid="bds-review-tasks"]').exists()).toBe(false);
		const cards = wrapper.findAll('[data-testid="bds-review-task-cards"] .bds-card');
		expect(cards).toHaveLength(5);
		expect(cards[2].text()).toContain("Confirm the current delivery location");
	});
});
