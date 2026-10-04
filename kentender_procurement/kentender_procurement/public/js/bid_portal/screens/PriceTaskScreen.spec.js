// BDS-CHG-001 v0.8 §10.11 behaviour of the price task: a changed price saves
// at once and the server's totals are read back; nothing is calculated in
// the page; an unpriced line says what is missing; a refused price is named
// in place.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import PriceTaskScreen from "./PriceTaskScreen.vue";
import { priceTask } from "./price.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor(call) {
	const route = ref({ path: `/tenders/${REF}/bid/price`, segments: ["tenders", REF, "bid", "price"], query: {} });
	const go = vi.fn();
	return { call, go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal) {
	return mount(PriceTaskScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
afterEach(() => {
	document.body.innerHTML = "";
});

describe("Price", () => {
	it("saves a changed unit price at once and shows the server's totals", async () => {
		const call = vi.fn(async (m) => (m.endsWith("get_bid_task") ? priceTask() : { ok: true }));
		const portal = portalFor(call);
		const wrapper = mountWith(priceTask("INCOMPLETE"), portal);
		expect(wrapper.get('[data-testid="bds-price-missing"]').text()).toBe("Enter the unit price before continuing.");
		expect(wrapper.get('[data-testid="bds-bid-total"]').text()).toBe("—");
		const unit = wrapper.get('[data-testid="bds-unit-price-1"]');
		await unit.setValue("160000");
		await unit.trigger("change");
		await flushPromises();
		expect([call.mock.calls[0][0].split(".").pop(), JSON.parse(call.mock.calls[0][1].values)]).toEqual(["save_bid_task", { "p-unit": "160000" }]);
		expect(wrapper.get('[data-testid="bds-bid-total"]').text()).toBe("KES 46,400,000.00");
	});

	it("saves a second entry made while the first is saving, never dropping it", async () => {
		let release;
		const first = new Promise((resolve) => (release = resolve));
		const call = vi.fn(async (m, args) => {
			if (m.endsWith("get_bid_task")) return priceTask("INCOMPLETE");
			if (call.mock.calls.filter((c) => c[0].endsWith("save_bid_task")).length === 1) await first;
			return { ok: true };
		});
		const wrapper = mountWith(priceTask("INCOMPLETE"), portalFor(call));
		await wrapper.get('[data-testid="bds-unit-price-1"]').setValue("160000");
		await wrapper.get('[data-testid="bds-tax-1"]').setValue("6400000");
		release();
		await flushPromises();
		await flushPromises();
		const saves = call.mock.calls.filter((c) => c[0].endsWith("save_bid_task")).map((c) => JSON.parse(c[1].values));
		expect(saves[0]).toEqual({ "p-unit": "160000" });
		expect(saves.some((v) => v["p-tax"] === "6400000")).toBe(true);
	});

	it("names a refused price in place and keeps it", async () => {
		const call = vi.fn(async () => ({ ok: false, errors: { "p-unit": "Enter an amount of at least 0.01." } }));
		const wrapper = mountWith(priceTask("INCOMPLETE"), portalFor(call));
		const unit = wrapper.get('[data-testid="bds-unit-price-1"]');
		await unit.setValue("-5");
		await unit.trigger("change");
		await flushPromises();
		expect(wrapper.text()).toContain("Enter an amount of at least 0.01.");
		expect(unit.element.value).toBe("-5");
	});

	it("with every line priced and saved, Save and continue opens the review", async () => {
		const call = vi.fn();
		const portal = portalFor(call);
		const wrapper = mountWith(priceTask(), portal);
		await wrapper.get('[data-testid="bds-price-save"]').trigger("click");
		expect(call).not.toHaveBeenCalled();
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/review`);
	});

	it("labels each row's amount as before tax, and tax and the Bid total once in the totals panel (BDS03-AC-015)", () => {
		const wrapper = mountWith(priceTask(), portalFor(vi.fn()));
		const headers = wrapper.findAll("thead th").map((th) => th.text());
		expect(headers).toContain("Line amount before tax");
		expect(headers.filter((h) => /total/i.test(h))).toEqual([]);
		const totals = wrapper.findAll(".bds-total-line").map((line) => line.find("span").text());
		expect(totals).toEqual(["Subtotal excluding tax", "Tax", "Bid total"]);
		expect(wrapper.findAll('[data-testid="bds-bid-total"]')).toHaveLength(1);
	});
});

