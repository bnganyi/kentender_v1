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
	it("numbers the tasks, marks the one to do next and says how far the preparation has got", async () => {
		const data = workspace();
		const states = ["Complete", "In progress", "Complete", "Complete", "Not started"];
		data.tasks = data.tasks.map((t, i) => ({
			...t, number: i + 1, status: states[i], next: i === 1,
			action: { href: t.action.href, label: ["Review", "Continue", "Review", "Review", "View"][i], primary: i === 1 },
		}));
		data.progress = { done: 3, of: 4, text: "3 of 4 tasks done", next: "Company and declarations" };
		const wrapper = mountWith({ initial: data }, portalFor({ call: vi.fn(async () => data) }));
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-workspace-progress"]').text()).toBe("3 of 4 tasks done · Next: Company and declarations");
		const rows = wrapper.findAll('[data-testid="bds-tasks-table"] tbody tr');
		expect(rows.map((r) => r.get(".bds-task-number").text())).toEqual(["1", "2", "3", "4", "5"]);
		expect(rows.map((r) => r.find('[data-testid="bds-task-next"]').exists())).toEqual([false, true, false, false, false]);
		expect(rows.map((r) => r.get("a").text())).toEqual(["Review", "Continue", "Review", "Review", "View"]);
		expect(rows.map((r) => r.get("a").classes().includes("btn-primary"))).toEqual([false, true, false, false, false]);
		globalThis.__narrow = true;
		const narrow = mountWith({ initial: data }, portalFor({ call: vi.fn(async () => data) }));
		await flushPromises();
		expect(narrow.findAll('[data-testid="bds-tasks-cards"] [data-testid="bds-task-next"]')).toHaveLength(1);
	});

	it("offers the preparer a way to notify the signatory, and nothing to the signatory", async () => {
		const handover = { signatories: ["Mary Wanjiku"], can_notify: true, last: null, wait_text: "", max_note: 500 };
		const wrapper = mountWith({ initial: { ...workspace(), handover } }, portalFor());
		await nextTick();
		expect(wrapper.get('[data-testid="bds-handover"] [data-testid="bds-handover-send"]').text()).toBe("Notify Mary Wanjiku");
		const signatory = mountWith({ initial: workspace() }, portalFor()); // the read carries no hand-over for the signatory
		await nextTick();
		expect(signatory.find('[data-testid="bds-handover"]').exists()).toBe(false);
	});

	it("hands the finished bid over: the preparer sees who signs, no Next task, and Review only as a view", async () => {
		const wrapper = mountWith({ initial: workspace() }, portalFor());
		await nextTick();
		expect(wrapper.get('[data-testid="bds-workspace-refs"]').text()).toContain("TND-MOH-2027-033 · BID-MOH-2027-033-001 · Draft Version 7");
		expect(wrapper.get('[data-testid="bds-workspace-action"]').text()).toBe("View complete bid");
		expect(wrapper.get('[data-testid="bds-workspace-action"]').classes()).not.toContain("btn-primary"); // he cannot submit: nothing here is the way on
		expect(wrapper.get('[data-testid="bds-workspace-progress"]').text()).toBe("4 of 4 tasks done · Mary Wanjiku signs and submits");
		expect(wrapper.find('[data-testid="bds-task-next"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="bds-task-note"]').text()).toBe("Mary Wanjiku signs and submits");
		expect(wrapper.get('[data-kt="next-step"]').text()).toContain("Authorised Signatory Mary Wanjiku must submit this bid.");
		expect(wrapper.get('[data-testid="bds-workspace-deadline"]').text()).toContain("Closes in 1 day 20 hours 40 minutes");
		expect(wrapper.findAll('[data-testid="bds-tasks-table"] tbody tr')).toHaveLength(5);
		expect(wrapper.get('[data-testid="bds-task-review"] a').text()).toBe("View");
		expect(wrapper.get('[data-testid="bds-task-review"] a').classes()).not.toContain("btn-primary");
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
		expect([action.text(), action.attributes("href"), action.classes().includes("btn-secondary")]).toEqual(["Back to My bids", "/my-bids", true]);
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
		const read = vi.fn(async () => { throw new Error("The server could not be reached."); });
		const failing = mountWith({ initial: null }, portalFor({ call: read }));
		await flushPromises();
		// the §10.17 Load failure state, and Try again reads once more
		const state = failing.get('[data-testid="bds-state-load-failure"]');
		expect([state.get("h1").text(), state.get("p").text()]).toEqual(["Bid could not be loaded", "Your saved bid has not changed."]);
		await state.get("button").trigger("click");
		await flushPromises();
		expect(read).toHaveBeenCalledTimes(2);
	});

	it("on a withdrawn Tender format keeps the tasks for reading, waits on the Procurement Officer and offers the two ways on", () => {
		const wrapper = mountWith({ initial: workspace("WITHDRAWN-RELEASE") }, portalFor());
		expect(wrapper.find('[data-testid="bds-workspace-action"]').exists()).toBe(false);
		expect(wrapper.get('[data-kt="next-step"]').text()).toContain("Procurement Officer Brian Wafula holds the governed Tender resolution");
		const links = wrapper.get('[data-testid="bds-guidance-links"]').findAll("a");
		expect(links.map((a) => [a.text(), a.attributes("href")])).toEqual([["View current Tender", `/tenders/${REF}`], ["Supplier support", "mailto:supplier.support@kentender.example"]]);
		expect(wrapper.findAll('[data-testid="bds-tasks-table"] tbody td a').map((a) => a.text())).toEqual(["View", "View", "View", "View", "View"]);
		expect(wrapper.text()).not.toMatch(/Continue bid|Review bid|Submit/);
	});
});
