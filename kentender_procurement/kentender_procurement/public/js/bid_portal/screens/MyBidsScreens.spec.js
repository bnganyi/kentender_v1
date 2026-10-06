// BDS-CHG-001 v0.8 §10.6 / §10.20 behaviour of My bids and Receipts: the
// read's rows and actions as sent, filters kept in the URL, a row command
// that opens the bid it changed, and the read-only suspended register.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import MyBidsScreen from "./MyBidsScreen.vue";
import ReceiptHistoryScreen from "./ReceiptHistoryScreen.vue";
import { myBids, receipts } from "./myBids.fixtures.js";

function portalFor({ call, path = "/my-bids", query = {} } = {}) {
	const route = ref({ path, segments: path.split("/").filter(Boolean), query });
	const go = vi.fn();
	return { call: call || vi.fn(async () => myBids()), go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(component, props, portal) {
	return mount(component, { props, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("My bids", () => {
	it("shows each row as the read words it, with its one action", () => {
		const wrapper = mountWith(MyBidsScreen, { initial: myBids() }, portalFor());
		const row = wrapper.get('[data-testid="bds-bid-row-BID-MOH-2027-033-001"]');
		expect(row.text()).toContain("Draft Version 7");
		expect(row.text()).toContain("Ready to submit");
		expect(row.get('[data-testid="bds-bid-action-0"]').text()).toBe("Review bid");
		expect(row.get('[data-testid="bds-bid-action-0"]').attributes("href")).toBe("/tenders/TND-MOH-2027-033/bid/review");
		expect(wrapper.get('[data-testid="kt-pager-count"]').text()).toBe("1 bid");
		expect(wrapper.find('[data-kt="journey"]').exists()).toBe(false); // a list, not a tracker
	});

	it("shows the preparer the action the server chose for a bid only the signatory can submit", () => {
		const data = myBids();
		data.rows[0] = { ...data.rows[0], actions: [{ label: "Hand over bid", href: "/tenders/TND-MOH-2027-033/bid" }], next_action: { label: "Hand over bid", href: "/tenders/TND-MOH-2027-033/bid" } };
		const wrapper = mountWith(MyBidsScreen, { initial: data }, portalFor());
		const action = wrapper.get('[data-testid="bds-bid-action-0"]');
		expect([action.text(), action.attributes("href")]).toEqual(["Hand over bid", "/tenders/TND-MOH-2027-033/bid"]);
	});

	it("keeps the filters in the URL and asks the server with them", async () => {
		const portal = portalFor();
		const wrapper = mountWith(MyBidsScreen, { initial: myBids() }, portal);
		await wrapper.get('[data-testid="bds-bids-status"]').setValue("Submitted");
		await flushPromises();
		expect(portal.go).toHaveBeenCalledWith("/my-bids", { replace: true, query: { search: "", status: "Submitted", organisation: "" }, keepFocus: true });
		expect(portal.call).toHaveBeenLastCalledWith("kentender_procurement.bid_submission.api.get_my_bids", { search: "", status: "Submitted", organisation: "" });
	});

	it("starts a replacement from a withdrawn bid and opens it", async () => {
		const call = vi.fn(async () => ({ ok: true }));
		const portal = portalFor({ call });
		const wrapper = mountWith(MyBidsScreen, { initial: myBids("WITHDRAWN") }, portal);
		const row = wrapper.get('[data-testid="bds-bid-row-BID-MOH-2027-041-001"]');
		expect(row.get('[data-testid="bds-bid-action-0"]').text()).toBe("View acknowledgement");
		await row.get('[data-testid="bds-bid-action-1"]').trigger("click");
		await flushPromises();
		const [method, args, opts] = call.mock.calls[0];
		expect([method, args.bid_reference, args.expected_record_version, opts]).toEqual(["kentender_procurement.bid_submission.api.prepare_replacement_bid", "BID-MOH-2027-041-001", 9, { type: "POST" }]);
		expect(portal.go).toHaveBeenCalledWith("/tenders/TND-MOH-2027-041/bid");
	});

	it("names a refused command in place and stays on the list", async () => {
		const call = vi.fn(async () => {
			throw new Error("The submission deadline has passed.");
		});
		const portal = portalFor({ call });
		const wrapper = mountWith(MyBidsScreen, { initial: myBids("WITHDRAWN") }, portal);
		await wrapper.get('[data-testid="bds-bid-action-1"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-load-failure"]').text()).toContain("The submission deadline has passed.");
		expect(portal.go).not.toHaveBeenCalled();
	});

	it("offers View Tenders when there are no bids, and Clear filters when filters hide them", async () => {
		const wrapper = mountWith(MyBidsScreen, { initial: myBids("EMPTY") }, portalFor());
		expect(wrapper.get('[data-testid="bds-bids-empty"]').text()).toContain("No bids yet. Find a Tender to start your first bid.");
		expect(wrapper.get('[data-testid="bds-bids-view-tenders"]').attributes("href")).toBe("/tenders");
		const filtered = mountWith(MyBidsScreen, { initial: myBids("EMPTY") }, portalFor({ query: { status: "Submitted" } }));
		expect(filtered.get('[data-testid="bds-bids-empty"]').text()).toContain("No bids match these filters.");
	});
});

describe("Receipts", () => {
	it("lists receipts and acknowledgements with their own View links and no bid actions", () => {
		const wrapper = mountWith(ReceiptHistoryScreen, { initial: receipts() }, portalFor({ path: "/account/receipts" }));
		expect(wrapper.get('[data-testid="bds-receipt-row-RCPT-MOH-2027-033-001"] a').attributes("href")).toBe("/tenders/TND-MOH-2027-033/bid/receipt/RCPT-MOH-2027-033-001");
		expect(wrapper.get('[data-testid="bds-receipt-row-WD-MOH-2027-041-001"]').text()).toContain("Withdrawn");
		expect(wrapper.text()).not.toMatch(/Start replacement|Withdraw bid|Prepare replacement/);
		expect(wrapper.get('[data-testid="bds-receipts-back"]').attributes("href")).toBe("/account");
	});

	it("keeps a suspended Account's receipts readable and says why nothing can change", () => {
		const wrapper = mountWith(ReceiptHistoryScreen, { initial: receipts("SUSPENDED") }, portalFor({ path: "/account/receipts" }));
		expect(wrapper.get('[data-testid="bds-receipts-suspended"]').text()).toBe("Account suspended");
		expect(wrapper.text()).toContain("You can read and download existing receipts");
		expect(wrapper.findAll("tbody tr")).toHaveLength(2);
	});

	it("masks another organisation's receipts as not found", async () => {
		const call = vi.fn(async () => ({ outcome: "NOT_FOUND" }));
		const wrapper = mountWith(ReceiptHistoryScreen, { initial: null }, portalFor({ call, path: "/account/receipts", query: { organisation: "ORG-OTHER" } }));
		await flushPromises();
		expect(call.mock.calls[0][1]).toEqual({ organisation: "ORG-OTHER" });
		expect(wrapper.emitted("not-found")).toHaveLength(1);
	});
});
