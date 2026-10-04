// BDS-CHG-001 v0.8 §10.8 behaviour of the documents task: Save and continue
// waits for the acknowledgement, saves it through SaveBidTask and opens the
// next task; a refusal is named in place and the tick kept; a failed notice
// offers Update notice email with verified emails only; Ask a question only
// while clarifications are open.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import DocumentsTaskScreen from "./DocumentsTaskScreen.vue";
import { documentsTask } from "./documents.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor({ call } = {}) {
	const route = ref({ path: `/tenders/${REF}/bid/documents`, segments: ["tenders", REF, "bid", "documents"], query: {} });
	const go = vi.fn();
	return { call: call || vi.fn(async () => ({ ok: true })), go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal) {
	return mount(DocumentsTaskScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Tender documents, clarifications and addenda", () => {
	it("waits for the acknowledgement, then saves it and opens the next task", async () => {
		const portal = portalFor();
		const wrapper = mountWith(documentsTask(), portal);
		const save = wrapper.get('[data-testid="bds-documents-save"]');
		expect(save.attributes("disabled")).toBeDefined();
		expect(wrapper.get('[data-testid="bds-documents-blocked"]').text()).toBe("Acknowledge the addendum to continue.");
		await wrapper.get('[data-testid="bds-acknowledge-ADD-MOH-2027-033-001"] input').setValue(true);
		expect(save.attributes("disabled")).toBeUndefined();
		await save.trigger("click");
		await flushPromises();
		const [method, args, opts] = portal.call.mock.calls[0];
		expect([method, args.task, JSON.parse(args.values), args.expected_record_version, opts]).toEqual(["kentender_procurement.bid_submission.api.save_bid_task", "documents", { "h-ack-1": true }, 12, { type: "POST" }]);
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/company`);
	});

	it("moves a Draft bound to an earlier definition first, then saves the tick on the re-read field", async () => {
		const before = documentsTask();
		before.addenda[0].acknowledgement = { ...before.addenda[0].acknowledgement, handle: "", moves_bid: true };
		const calls = [];
		const call = vi.fn(async (method, args) => {
			calls.push([method.split(".").pop(), args.values]);
			if (method.endsWith("get_bid_task")) return documentsTask();
			return calls.length === 1 ? { ok: false, code: "BDS_ADDENDUM_REVIEW_REQUIRED", refreshed: true } : { ok: true };
		});
		const portal = portalFor({ call });
		const wrapper = mountWith(before, portal);
		await wrapper.get('[data-testid="bds-acknowledge-ADD-MOH-2027-033-001"] input').setValue(true);
		await wrapper.get('[data-testid="bds-documents-save"]').trigger("click");
		await flushPromises();
		expect(calls).toEqual([["save_bid_task", "{}"], ["get_bid_task", undefined], ["save_bid_task", JSON.stringify({ "h-ack-1": true })]]);
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/company`);
	});

	it("names a refused acknowledgement in place and keeps the tick", async () => {
		const call = vi.fn(async () => ({ ok: false, errors: { "h-ack-1": "Confirm the addendum acknowledgement." } }));
		const portal = portalFor({ call });
		const wrapper = mountWith(documentsTask(), portal);
		await wrapper.get('[data-testid="bds-acknowledge-ADD-MOH-2027-033-001"] input').setValue(true);
		await wrapper.get('[data-testid="bds-documents-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.text()).toContain("Confirm the addendum acknowledgement.");
		expect(wrapper.get('[data-testid="bds-acknowledge-ADD-MOH-2027-033-001"] input').element.checked).toBe(true);
		expect(portal.go).not.toHaveBeenCalled();
	});

	it("with nothing to acknowledge, Save and continue simply opens the next task", async () => {
		const portal = portalFor();
		const wrapper = mountWith(documentsTask("OPEN"), portal);
		expect(wrapper.find('[data-testid="bds-documents-badge"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="bds-task-no-addenda"]').text()).toBe("No addenda have been issued.");
		await wrapper.get('[data-testid="bds-documents-save"]').trigger("click");
		expect(portal.call).not.toHaveBeenCalled();
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/company`);
		await wrapper.get('[data-testid="bds-task-ask"]').trigger("click");
		await nextTick();
		expect(document.querySelector('[data-testid="bds-question-dialog"]')).not.toBeNull();
	});

	it("shows the acknowledgement's author once acknowledged", () => {
		const wrapper = mountWith(documentsTask("COMPLETE"), portalFor());
		expect(wrapper.get('[data-testid="bds-acknowledged"]').text()).toBe("Acknowledged by David Ouma on 1 Jun 2027, 12:10 EAT");
		expect(wrapper.get('[data-testid="bds-documents-badge"]').text()).toBe("Complete");
	});

	it("names a failed notice and changes the notice email to another verified email", async () => {
		const call = vi.fn(async (method) => (method.endsWith("get_bid_task") ? documentsTask("NOTICE-FAILED") : { ok: true, changed: true }));
		const portal = portalFor({ call });
		const wrapper = mountWith(documentsTask("NOTICE-FAILED"), portal);
		expect(wrapper.get('[data-testid="bds-addendum-notice-ADD-MOH-2027-033-001"]').text()).toContain("Delivery problem");
		await wrapper.get('[data-testid="bds-update-notice-email"]').trigger("click");
		await nextTick();
		const options = [...document.querySelectorAll('[data-testid="bds-notice-contact-choice"] option')].map((o) => o.textContent);
		expect(options).toEqual(["tenders@afyadigital.example", "bids@afyadigital.example"]);
		const select = wrapper.get('[data-testid="bds-notice-contact-choice"]');
		await select.setValue("C2");
		await wrapper.get('[data-testid="bds-notice-contact-save"]').trigger("click");
		await flushPromises();
		expect(call.mock.calls[0][0]).toBe("kentender_procurement.bid_submission.api.update_tender_notice_contact");
		expect(call.mock.calls[0][1]).toMatchObject({ bidder_arrangement_id: "ARR-MOH-2027-033-001", notice_contact_id: "C2", expected_record_version: 3 });
		expect(call.mock.calls[1][0]).toBe("kentender_procurement.bid_submission.api.get_bid_task"); // the page reloads in place
		expect(document.querySelector('[data-testid="bds-notice-contact-dialog"]')).toBeNull();
	});

	it("keeps Queued and Sent notices as information, never as proof, and never blocks reading", () => {
		for (const [variant, status] of [["NOTICE-QUEUED", "Queued"], ["NOTICE-SENT", "Sent"]]) {
			const wrapper = mountWith(documentsTask(variant), portalFor());
			expect(wrapper.get('[data-testid="bds-addendum-notice-ADD-MOH-2027-033-001"]').text()).toContain(status);
			expect(wrapper.find('[data-testid="bds-update-notice-email"]').exists()).toBe(false);
			expect(wrapper.findAll('[data-testid="bds-task-documents-table"] tbody tr')).toHaveLength(2);
			wrapper.unmount();
		}
	});
});
