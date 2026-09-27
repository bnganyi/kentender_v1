// BDS-CHG-001 v0.8 §11.5 View status: the read names one §10.17 state;
// Confirmation pending's View status reads again; an accepted attempt goes
// straight to its receipt; a rejection offers Try confirmation again only
// when the server permits one.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import StatusScreen from "./StatusScreen.vue";

const REF = "TND-MOH-2027-033";
const PATH = `/tenders/${REF}/bid/status`;
const pending = { page: { title: "Submission status", back_href: `/tenders/${REF}/bid` }, redirect: "", state: { key: "confirmation-pending", figures: { correlation_id: "COR-BDS-2027-033-01", support_reference: "SUP-BDS-2027-033-01" }, href: PATH, retry: false } };
function portalFor(call) {
	const route = ref({ path: PATH, segments: ["tenders", REF, "bid", "status"], query: {} });
	const go = vi.fn();
	return { call, go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal) {
	return mount(StatusScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
afterEach(() => {
	document.body.innerHTML = "";
});

describe("View status", () => {
	it("names a pending attempt by its correlation and reads again on View status", async () => {
		const call = vi.fn(async () => pending);
		const wrapper = mountWith(pending, portalFor(call));
		const state = wrapper.get('[data-testid="bds-state-confirmation-pending"]');
		expect(state.get("h1").text()).toBe("Submission confirmation is still pending. Do not submit again.");
		expect(state.get("p").text()).toContain("Correlation COR-BDS-2027-033-01; support reference SUP-BDS-2027-033-01.");
		await state.get("button").trigger("click");
		await flushPromises();
		expect(call).toHaveBeenCalledTimes(1);
	});

	it("goes straight to the receipt of an accepted attempt", async () => {
		const portal = portalFor(vi.fn(async () => ({ redirect: `/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-001` })));
		mountWith(null, portal);
		await flushPromises();
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-001`);
	});

	it("offers Try confirmation again after a rejection only when the server permits a new attempt", () => {
		const rejected = (retry) => ({ ...pending, state: { key: "custody-rejected", figures: { rejection_reference: "TBX-REJECT-033-01", current_time: "10 Jun 2027, 14:30:05 EAT", deadline: "12 Jun 2027, 11:00 EAT" }, href: retry ? `/tenders/${REF}/bid/submit` : "mailto:support@example.test", retry } });
		const allowed = mountWith(rejected(true), portalFor(vi.fn()));
		expect(allowed.get("a").text()).toBe("Try confirmation again");
		expect(allowed.get("a").attributes("href")).toBe(`/tenders/${REF}/bid/submit`);
		const refused = mountWith(rejected(false), portalFor(vi.fn()));
		expect(refused.get("a").text()).toBe("Contact support");
	});
});
