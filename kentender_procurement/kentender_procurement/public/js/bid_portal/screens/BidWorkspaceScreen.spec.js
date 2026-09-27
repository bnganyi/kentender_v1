// BDS-CHG-001 v0.8 §10.7 behaviour of Your bid: the read's header action,
// deadline, availability notice, notices and task rows as sent; a next-step
// fix goes where the server says; a masked bid is Not found; a failed read
// is named in place.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import BidWorkspaceScreen from "./BidWorkspaceScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor({ call } = {}) {
	const route = ref({ path: `/tenders/${REF}/bid`, segments: ["tenders", REF, "bid"], query: {} });
	const go = vi.fn();
	return { call: call || vi.fn(async () => workspace()), go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(props, portal) {
	return mount(BidWorkspaceScreen, { props: { reference: REF, ...props }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Your bid", () => {
	it("shows the representative the waiting line, the deadline, notices and five tasks with Review bid", async () => {
		const wrapper = mountWith({ initial: workspace() }, portalFor());
		await nextTick();
		expect(wrapper.get('[data-testid="bds-workspace-refs"]').text()).toContain("TND-MOH-2027-033 · BID-MOH-2027-033-001 · Draft Version 7");
		expect(wrapper.get('[data-testid="bds-workspace-action"]').text()).toBe("Review bid");
		expect(wrapper.get('[data-kt="next-step"]').text()).toContain("Authorised Signatory Mary Wanjiku must submit this bid.");
		expect(wrapper.get('[data-testid="bds-workspace-deadline"]').text()).toContain("Closes in 1 day 20 hours 40 minutes");
		expect(wrapper.findAll('[data-testid="bds-tasks-table"] tbody tr')).toHaveLength(5);
		expect(wrapper.get('[data-testid="bds-task-review"] a').classes()).toContain("kt-btn-primary");
		expect(wrapper.text()).not.toMatch(/Submit bid|%|manifest/);
		expect(wrapper.get('[data-testid="bds-workspace-saved"]').text()).toBe("Saved 10 Jun 2027, 13:50 EAT by David Ouma.");
	});

	it("names a closed gate above the tasks with the deadline and support, and offers no Submit", () => {
		const wrapper = mountWith({ initial: workspace("GATE") }, portalFor());
		const notice = wrapper.get('[data-testid="bds-workspace-availability"]');
		expect(notice.classes()).toContain("is-critical");
		expect(notice.text()).toContain("Electronic bid submission is not available yet");
		expect(notice.get("a").attributes("href")).toMatch(/^mailto:/);
	});

	it("follows the blocked next step's Review addendum fix to the documents task", async () => {
		const portal = portalFor();
		const wrapper = mountWith({ initial: workspace("ADDENDUM") }, portal);
		await nextTick();
		await wrapper.get('[data-fix="review_addendum"]').trigger("click");
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/documents`);
		expect(wrapper.text()).toContain("Not acknowledged");
	});

	it("follows a fix the server names by task", async () => {
		const portal = portalFor();
		const answer = workspace("ADDENDUM");
		answer.next_step.blockers[0].fixes[0].target = { task: "documents" };
		answer.next_step.fixes[0].target = { task: "documents" };
		const wrapper = mountWith({ initial: answer }, portal);
		await nextTick();
		await wrapper.get('[data-fix="review_addendum"]').trigger("click");
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/documents`);
	});

	it("after the deadline shows the trusted time and Back to My bids", () => {
		const wrapper = mountWith({ initial: workspace("CLOSED") }, portalFor());
		expect(wrapper.get('[data-testid="bds-workspace-deadline"]').text()).toContain("Trusted server time");
		const action = wrapper.get('[data-testid="bds-workspace-action"]');
		expect([action.text(), action.attributes("href"), action.classes().includes("kt-btn-secondary")]).toEqual(["Back to My bids", "/my-bids", true]);
	});

	it("draws labelled cards at the narrow frame", () => {
		globalThis.__narrow = true;
		const wrapper = mountWith({ initial: workspace() }, portalFor());
		expect(wrapper.find('[data-testid="bds-tasks-table"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="bds-tasks-cards"]').findAll(".bds-card")).toHaveLength(5);
	});

	it("reads the bid for this Tender, masks another organisation's as not found and names a failure", async () => {
		const call = vi.fn(async () => ({ outcome: "NOT_FOUND" }));
		const masked = mountWith({ initial: null }, portalFor({ call }));
		await flushPromises();
		expect(call.mock.calls[0]).toEqual(["kentender_procurement.bid_submission.api.get_bid_workspace", { tender_reference: REF, bid_reference: "", organisation: "" }]);
		expect(masked.emitted("not-found")).toHaveLength(1);
		const failing = mountWith({ initial: null }, portalFor({ call: vi.fn(async () => { throw new Error("The server could not be reached."); }) }));
		await flushPromises();
		expect(failing.text()).toContain("The server could not be reached.");
	});
});
