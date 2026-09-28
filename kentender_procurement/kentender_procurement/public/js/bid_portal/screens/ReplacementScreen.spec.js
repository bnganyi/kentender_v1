// BDS-CHG-001 v0.8 §10.15 behaviour of Prepare replacement bid: Create
// replacement Draft runs `PrepareReplacementBid` once and opens the new Draft
// as the bid; a refusal re-reads and is named; once a Draft is open the page
// leads to it and offers no second Create.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import ReplacementScreen from "./ReplacementScreen.vue";
import { replacementPage } from "./replacement.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor(call = vi.fn()) {
	const route = ref({ path: `/tenders/${REF}/bid/replace`, segments: ["tenders", REF, "bid", "replace"], query: {} });
	const go = vi.fn();
	return { call, go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal = portalFor()) {
	return mount(ReplacementScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
afterEach(() => {
	document.body.innerHTML = "";
});

describe("Prepare replacement bid", () => {
	it("creates the replacement Draft once and opens it as the bid", async () => {
		const call = vi.fn(async () => ({ ok: true, status: "Ready to submit", started_from: "Submitted" }));
		const portal = portalFor(call);
		const wrapper = mountWith(replacementPage(), portal);
		expect(wrapper.get('[data-testid="bds-replacement-notice"] a').attributes("href")).toBe(`/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-001`);
		await wrapper.get('[data-testid="bds-replacement-create"]').trigger("click");
		await flushPromises();
		expect([call.mock.calls[0][0].split(".").pop(), call.mock.calls[0][1].expected_record_version]).toEqual(["prepare_replacement_bid", 61]);
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid`);
	});

	it("names a refusal and re-reads", async () => {
		const call = vi.fn().mockResolvedValueOnce({ ok: false, message: "Submission changes closed at the deadline." }).mockResolvedValueOnce(replacementPage("OPEN"));
		const wrapper = mountWith(replacementPage(), portalFor(call));
		await wrapper.get('[data-testid="bds-replacement-create"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-load-failure"]').text()).toBe("Submission changes closed at the deadline.");
		expect(wrapper.find('[data-testid="bds-replacement-create"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="bds-replacement-continue"]').attributes("href")).toBe(`/tenders/${REF}/bid`);
	});

	it.each([
		["BDS_REPLACEMENT_CONFLICT", "replacement-conflict", { current_receipt: "RCPT-MOH-2027-033-002" }, "a", "View current receipt"],
		["BDS_IDEMPOTENCY_CONFLICT", "idempotency-conflict", {}, "button", "Refresh"],
		["BDS_STALE_VERSION", "stale-draft", {}, "button", "Reload"],
	])("shows %s as its catalogue state with its one way on (BDS03-AC-011, BDS04-AC-002)", async (code, key, detail, control, label) => {
		const refused = Object.assign(new Error("refused"), { code, detail });
		const call = vi.fn(async (method) => {
			if (method.endsWith("prepare_replacement_bid")) throw refused;
			return replacementPage();
		});
		const wrapper = mountWith(replacementPage(), portalFor(call));
		await wrapper.get('[data-testid="bds-replacement-create"]').trigger("click");
		await flushPromises();
		const state = wrapper.get(`[data-testid="bds-state-${key}"]`);
		const action = state.get(control);
		expect(action.text()).toBe(label);
		if (control === "a") expect(action.attributes("href")).toBe(`/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-002`);
		else {
			const before = call.mock.calls.length;
			await action.trigger("click");
			await flushPromises();
			expect(call.mock.calls.slice(before).map(([m]) => m.split(".").pop())).toContain("get_replacement_page");
			expect(wrapper.find(`[data-testid="bds-state-${key}"]`).exists()).toBe(false);
		}
	});
});

