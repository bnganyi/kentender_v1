// BDS-CHG-001 v0.8 §10.14–10.15 behaviour of the receipt page: the read
// decides which actions show; Withdraw bid opens the dialog, a refused reason
// is named in place, and an acknowledged withdrawal opens its
// acknowledgement; the representative only reads, prints and downloads; a
// replacement receipt links the Version it superseded.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import ReceiptScreen from "./ReceiptScreen.vue";
import { acknowledgementPage, receiptPage } from "./receipt.fixtures.js";

function portalFor(call = vi.fn(), query = {}) {
	const route = ref({ path: "/tenders/x/bid/receipt/y", segments: ["tenders", "x", "bid", "receipt", "y"], query });
	const go = vi.fn();
	return { call, go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal = portalFor()) {
	const document = (initial.receipt || initial.acknowledgement)[0].value;
	return mount(ReceiptScreen, { props: { reference: initial.bid.tender_reference, receipt: document, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Receipt", () => {
	it("offers the signatory both changes, and Print opens the receipt on its own", () => {
		const wrapper = mountWith(receiptPage());
		expect(wrapper.get('[data-testid="bds-receipt-prepare_replacement"]').attributes("href")).toBe("/tenders/TND-MOH-2027-033/bid/replace");
		expect(wrapper.get('[data-testid="bds-receipt-withdraw"]').text()).toBe("Withdraw bid");
		const print = wrapper.get('[data-testid="bds-receipt-print"]');
		expect([print.attributes("target"), print.attributes("href")]).toEqual(["_blank", expect.stringContaining("inline=1")]);
		expect(wrapper.get('[data-testid="bds-receipt-sentence"]').text()).toContain("remains valid until a replacement is accepted");
	});

	it("names a refused reason in place, then opens the acknowledgement once withdrawn", async () => {
		const call = vi
			.fn()
			.mockResolvedValueOnce({ ok: false, errors: { reason: "Enter 10–500 characters." } })
			.mockResolvedValueOnce({ ok: true, acknowledgement_reference: "WD-MOH-2027-033-001" });
		const portal = portalFor(call);
		const wrapper = mountWith(receiptPage(), portal);
		await wrapper.get('[data-testid="bds-receipt-withdraw"]').trigger("click");
		const dialog = wrapper.get('[data-testid="bds-withdraw-dialog"]');
		expect(dialog.findAll(".bds-dialog-fact .kt-label").map((l) => l.text())).toEqual(["Tender", "Bid", "Current receipt", "Deadline"]);
		await dialog.get('[data-testid="bds-withdraw-reason"]').setValue("Too short");
		await dialog.get('[data-testid="bds-withdraw-confirm"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-withdraw-error"]').text()).toBe("Enter 10–500 characters.");
		expect(call.mock.calls[0][1]).toMatchObject({ receipt_reference: "RCPT-MOH-2027-033-001", reason: "Too short", confirmed: 1 });
		await dialog.get('[data-testid="bds-withdraw-reason"]').setValue("Our pricing changed; we will submit a corrected bid.");
		await dialog.get('[data-testid="bds-withdraw-confirm"]').trigger("click");
		await flushPromises();
		expect(call.mock.calls[1][1].idempotency_key).toBe(call.mock.calls[0][1].idempotency_key);
		expect(portal.go).toHaveBeenCalledWith("/tenders/TND-MOH-2027-033/bid/receipt/WD-MOH-2027-033-001");
	});

	it("stacks the three header actions on a narrow screen (board D at 390)", () => {
		globalThis.__narrow = true;
		const wrapper = mountWith(receiptPage());
		expect(wrapper.get('[data-testid="bds-receipt-actions"]').classes()).toContain("bds-actions-stack");
		expect(wrapper.findAll('[data-testid="bds-receipt-actions"] .btn').every((b) => b.classes().includes("bds-btn-block"))).toBe(true);
	});

	it("lets the representative only read, print and download", () => {
		const wrapper = mountWith(receiptPage("REPRESENTATIVE"));
		expect(wrapper.findAll('[data-testid="bds-receipt-actions"] .btn').map((b) => b.text())).toEqual(["Print receipt"]);
		expect(wrapper.find('[data-testid="bds-receipt-sentence"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="bds-receipt-download"]').attributes("href")).toContain("download_bid_receipt");
	});

	it("opens the withdrawal dialog when the bid page's Withdraw bid leads here", async () => {
		const wrapper = mountWith(receiptPage(), portalFor(vi.fn(), { action: "withdraw" }));
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-withdraw-dialog"]').exists()).toBe(true);
		const representative = mountWith(receiptPage("REPRESENTATIVE"), portalFor(vi.fn(), { action: "withdraw" }));
		await flushPromises();
		expect(representative.find('[data-testid="bds-withdraw-dialog"]').exists()).toBe(false);
	});

	it("shows a withdrawal acknowledgement, and Start replacement opens the new Draft", async () => {
		const call = vi.fn(async () => ({ ok: true, status: "Ready to submit", started_from: "Withdrawn" }));
		const portal = portalFor(call);
		const wrapper = mountWith(acknowledgementPage(), portal);
		expect(wrapper.get("h1").text()).toBe("Bid withdrawn");
		expect(wrapper.get('[data-testid="bds-acknowledgement-download"]').attributes("href")).toContain("download_withdrawal_acknowledgement");
		await wrapper.get('[data-testid="bds-start-replacement"]').trigger("click");
		await flushPromises();
		expect(call.mock.calls[0][0].split(".").pop()).toBe("prepare_replacement_bid");
		expect(portal.go).toHaveBeenCalledWith("/tenders/TND-MOH-2027-041/bid");
		const reader = mountWith(acknowledgementPage({ signatory: false }));
		expect(reader.find('[data-testid="bds-start-replacement"]').exists()).toBe(false);
	});

	it("links the Version a replacement superseded", () => {
		const wrapper = mountWith(receiptPage("REPLACED"));
		expect(wrapper.get("h1").text()).toBe("Replacement bid submitted");
		const lineage = wrapper.get('[data-testid="bds-receipt-lineage"]');
		expect([lineage.get(".kt-status").text(), lineage.get("a").attributes("href")]).toEqual(["Version 1 superseded", "/tenders/TND-MOH-2027-033/bid/receipt/RCPT-MOH-2027-033-001"]);
	});
});
