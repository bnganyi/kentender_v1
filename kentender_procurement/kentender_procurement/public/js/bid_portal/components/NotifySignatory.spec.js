// Handing a finished bid over: the preparer tells the Authorised Signatory it is
// ready. The read decides who is waiting and whether another message may go; the
// server decides what is refused. Here: what is shown, what is sent, what is said back.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import NotifySignatory from "./NotifySignatory.vue";

const HANDOVER = { signatories: ["Mary Wanjiku"], can_notify: true, last: null, wait_text: "", max_note: 500 };
const BID = { reference: "BID-1" };

function mountWith(handover, call) {
	const portal = { call: call || vi.fn(async () => ({ ok: true, recipients: ["Mary Wanjiku"], notified_at: "20 May 2027, 11:05 EAT" })), createCommandRunner };
	const wrapper = mount(NotifySignatory, { props: { handover, bid: BID }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: (s, args = []) => s.replace(/\{(\d+)\}/g, (_, i) => args[i]) } } } });
	return { wrapper, portal };
}
afterEach(() => {
	document.body.innerHTML = "";
});

describe("Hand over to the signatory", () => {
	it("names who is waiting and offers to notify them with an optional message", () => {
		const { wrapper } = mountWith(HANDOVER);
		expect(wrapper.get("h2").text()).toBe("Hand over to the signatory");
		expect(wrapper.text()).toContain("Mary Wanjiku has it waiting in My bids");
		expect(wrapper.get('[data-testid="bds-handover-send"]').text()).toBe("Notify Mary Wanjiku");
		expect(wrapper.get('[data-testid="bds-handover-note"]').attributes("maxlength")).toBe("500");
	});

	it("sends the message with the bid, says who was told, and asks the page to re-read", async () => {
		const { wrapper, portal } = mountWith(HANDOVER);
		await wrapper.get('[data-testid="bds-handover-note"]').setValue("Please sign before Friday.");
		await wrapper.get('[data-testid="bds-handover-send"]').trigger("click");
		await flushPromises();
		const [method, params, options] = portal.call.mock.calls[0];
		expect(method).toBe("kentender_procurement.bid_submission.api.notify_signatory");
		expect(params).toMatchObject({ bid_reference: "BID-1", note: "Please sign before Friday." });
		expect(params.idempotency_key).toMatch(/^bds-notify-/);
		expect(options).toEqual({ type: "POST" });
		expect(wrapper.get('[data-testid="bds-handover-sent"]').text()).toBe("Mary Wanjiku was notified 20 May 2027, 11:05 EAT.");
		expect(wrapper.emitted("sent")).toHaveLength(1);
		expect(wrapper.get('[data-testid="bds-handover-note"]').element.value).toBe(""); // the message was sent
	});

	it("shows a refusal where it applies and keeps what was typed", async () => {
		const call = vi.fn(async () => ({ ok: false, message: "Check the highlighted value.", errors: { notify: "Mary Wanjiku was already notified. You can send another reminder after 20 May 2027, 11:10 EAT." } }));
		const { wrapper } = mountWith(HANDOVER, call);
		await wrapper.get('[data-testid="bds-handover-note"]').setValue("Soon please");
		await wrapper.get('[data-testid="bds-handover-send"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-handover-error"]').text()).toContain("You can send another reminder after");
		expect(wrapper.get('[data-testid="bds-handover-note"]').element.value).toBe("Soon please");
		expect(wrapper.emitted("sent")).toBeUndefined();
	});

	it("says when they were last told and, while another message cannot go yet, why and when", () => {
		const waiting = { ...HANDOVER, can_notify: false, last: { by: "David Ouma", at_label: "20 May 2027, 11:00 EAT" }, wait_text: "You can send another reminder after 20 May 2027, 11:10 EAT." };
		const { wrapper } = mountWith(waiting);
		expect(wrapper.get('[data-testid="bds-handover-last"]').text()).toBe("Last notified 20 May 2027, 11:00 EAT by David Ouma.");
		expect(wrapper.get('[data-testid="bds-handover-wait"]').text()).toBe("You can send another reminder after 20 May 2027, 11:10 EAT.");
		expect(wrapper.find('[data-testid="bds-handover-send"]').exists()).toBe(false);
	});
});
