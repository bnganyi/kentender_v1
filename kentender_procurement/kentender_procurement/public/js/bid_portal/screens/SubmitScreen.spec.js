// BDS-CHG-001 v0.8 §10.13 behaviour of Submit bid: Submit stays disabled
// until the final confirmation is ticked; the dialog confirms, then the page
// prepares the signature, signs through the test trust service and submits
// with one request key; success opens the receipt, an uncertain attempt
// re-reads into the pending state; Try confirmation again brings the
// confirmation back; Check certificate is a fresh read.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import SubmitScreen from "./SubmitScreen.vue";
import { submitPage } from "./submit.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor(call) {
	const route = ref({ path: `/tenders/${REF}/bid/submit`, segments: ["tenders", REF, "bid", "submit"], query: {} });
	const go = vi.fn();
	return { call, go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal) {
	return mount(SubmitScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
const method = (m) => m.split(".").pop();
afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Submit bid", () => {
	it("confirms, signs and submits with one request key, then opens the receipt", async () => {
		const call = vi.fn(async (m) => ({
			prepare_bid_signature: { ok: true, signing_request: "SIG-REQ-1", simulation: true },
			sign_with_test_trust_service: { signature: "SIG-1" },
			submit_bid: { ok: true, status: "Submitted", receipt_reference: "RCPT-MOH-2027-033-001" },
		})[method(m)]);
		const portal = portalFor(call);
		const wrapper = mountWith(submitPage(), portal);
		const open = wrapper.get('[data-testid="bds-submit-open"]');
		expect(open.attributes("disabled")).toBeDefined();
		await wrapper.get('[data-testid="bds-submit-confirmation"]').setValue(true);
		expect(open.attributes("disabled")).toBeUndefined();
		await open.trigger("click");
		const dialog = wrapper.get('[data-testid="bds-submit-dialog"]');
		expect(dialog.get('[role="dialog"]').attributes("aria-labelledby")).toBe("bds-submit-dialog-title");
		expect(dialog.findAll(".bds-dialog-fact .kt-label").map((l) => l.text())).toEqual(["Tender", "Bidder", "Bid total", "Deadline"]);
		await wrapper.get('[data-testid="bds-submit-confirm"]').trigger("click");
		await flushPromises();
		expect(call.mock.calls.map((c) => method(c[0]))).toEqual(["prepare_bid_signature", "sign_with_test_trust_service", "submit_bid"]);
		const submitted = call.mock.calls[2][1];
		expect([submitted.signature, submitted.confirmed, submitted.expected_record_version]).toEqual(["SIG-1", 1, 52]);
		expect(submitted.idempotency_key).toMatch(/^bds-submit-/);
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-001`);
	});

	it("re-reads into the pending state when the tender box has not answered", async () => {
		const call = vi.fn(async (m) => ({
			prepare_bid_signature: { ok: true, signing_request: "SIG-REQ-1", simulation: true },
			sign_with_test_trust_service: { signature: "SIG-1" },
			submit_bid: { ok: false, code: "BDS_SUBMISSION_UNCERTAIN", correlation_id: "COR-BDS-2027-033-01" },
			get_submit_page: submitPage("PENDING"),
		})[method(m)]);
		const portal = portalFor(call);
		const wrapper = mountWith(submitPage(), portal);
		await wrapper.get('[data-testid="bds-submit-confirmation"]').setValue(true);
		await wrapper.get('[data-testid="bds-submit-open"]').trigger("click");
		await wrapper.get('[data-testid="bds-submit-confirm"]').trigger("click");
		await flushPromises();
		expect(portal.go).not.toHaveBeenCalled();
		expect(wrapper.find('[data-testid="bds-submit-dialog"]').exists()).toBe(false);
		const pending = wrapper.get('[data-testid="bds-submit-pending"]');
		expect(pending.get("a").attributes("href")).toBe(`/tenders/${REF}/bid/status`);
		expect(pending.get("button").attributes("disabled")).toBeDefined();
		expect(wrapper.find('[data-testid="bds-submit-open"]').exists()).toBe(false);
	});

	it("keeps a refused submission named after the page re-reads", async () => {
		const call = vi.fn(async (m) => {
			if (method(m) === "prepare_bid_signature") throw Object.assign(new Error("An addendum changed this Tender; review it before submitting."), { code: "BDS_ADDENDUM_REVIEW_REQUIRED" });
			return submitPage();
		});
		const wrapper = mountWith(submitPage(), portalFor(call));
		await wrapper.get('[data-testid="bds-submit-confirmation"]').setValue(true);
		await wrapper.get('[data-testid="bds-submit-open"]').trigger("click");
		await wrapper.get('[data-testid="bds-submit-confirm"]').trigger("click");
		await flushPromises();
		expect(call.mock.calls.map((c) => method(c[0]))).toEqual(["prepare_bid_signature", "get_submit_page"]);
		expect(wrapper.get('[data-testid="bds-load-failure"]').text()).toBe("An addendum changed this Tender; review it before submitting.");
	});

	it("shows another person's change in place of the confirmation, and Reload reads again", async () => {
		const call = vi.fn(async (m) => {
			if (method(m) === "prepare_bid_signature") throw Object.assign(new Error("Another person changed this bid. Reload before continuing."), { code: "BDS_STALE_VERSION", detail: {} });
			return submitPage();
		});
		const wrapper = mountWith(submitPage(), portalFor(call));
		await wrapper.get('[data-testid="bds-submit-confirmation"]').setValue(true);
		await wrapper.get('[data-testid="bds-submit-open"]').trigger("click");
		await wrapper.get('[data-testid="bds-submit-confirm"]').trigger("click");
		await flushPromises();
		const state = wrapper.get('[data-testid="bds-state-stale-draft"]');
		expect(wrapper.find('[data-testid="bds-submit-decision"]').exists()).toBe(false);
		await state.get("button").trigger("click");
		await flushPromises();
		expect(call.mock.calls.map((c) => method(c[0]))).toEqual(["prepare_bid_signature", "get_submit_page", "get_submit_page"]);
		expect(wrapper.find('[data-testid="bds-state-stale-draft"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="bds-submit-decision"]').exists()).toBe(true);
	});

	it("is replaced by Deadline passed for a bid that was not submitted in time", () => {
		const closed = { ...submitPage(), state: { key: "deadline-passed", figures: { deadline: "12 Jun 2027, 11:00 EAT", current_time: "12 Jun 2027, 11:00:01 EAT" }, href: "/my-bids", retry: false } };
		const wrapper = mountWith(closed, portalFor(vi.fn()));
		const state = wrapper.get('[data-testid="bds-state-deadline-passed"]');
		expect(state.get("p").text()).toBe("Deadline 12 Jun 2027, 11:00 EAT; trusted server time 12 Jun 2027, 11:00:01 EAT.");
		expect(state.get("a").attributes("href")).toBe("/my-bids");
		expect(wrapper.find('[data-testid="bds-submit"]').exists()).toBe(false);
	});

	it("brings the confirmation back only when the signatory tries again after a rejection", async () => {
		const wrapper = mountWith(submitPage("REJECTED"), portalFor(vi.fn()));
		expect(wrapper.find('[data-testid="bds-submit-decision"]').exists()).toBe(false);
		await wrapper.findAll("button").find((b) => b.text() === "Try confirmation again").trigger("click");
		expect(wrapper.get('[data-testid="bds-submit-decision"]').exists()).toBe(true);
		expect(wrapper.get('[data-testid="bds-submit-open"]').attributes("disabled")).toBeDefined();
	});

	it("checks the certificate again with a fresh read", async () => {
		const call = vi.fn(async (m) => (method(m) === "check_certificate" ? { status: "Required", text: "A valid digital signature certificate is required before you can submit." } : submitPage("CERTIFICATE")));
		const wrapper = mountWith(submitPage("CERTIFICATE"), portalFor(call));
		expect(wrapper.find('[data-testid="bds-submit-decision"]').exists()).toBe(false);
		await wrapper.findAll("button").find((b) => b.text() === "Check certificate").trigger("click");
		await flushPromises();
		expect(call.mock.calls.map((c) => method(c[0]))).toEqual(["check_certificate", "get_submit_page"]);
		expect(wrapper.get('[data-testid="bds-certificate-check"]').text()).toBe("A valid digital signature certificate is required before you can submit.");
	});

	it("names a closed production switch with support and offers only Back to bid", () => {
		const wrapper = mountWith(submitPage("GATE"), portalFor(vi.fn()));
		const notice = wrapper.get('[data-testid="bds-submit-notice"]');
		expect(notice.get("strong").text()).toBe("Electronic bid submission is not available yet");
		expect(notice.findAll("a").map((a) => a.text())).toEqual(["Supplier support"]);
		expect(wrapper.get('[data-testid="bds-submit-action"]').text()).toBe("Back to bid");
		expect(wrapper.find('[data-testid="bds-submit-decision"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="bds-submit-consequence"]').exists()).toBe(false);
	});
});
