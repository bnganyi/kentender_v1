// BDS-CHG-001 v0.8 §10.10 behaviour of the requirements task: a row opens the
// response drawer with that requirement's fields; the attention notice opens
// the row to fix; Save and continue saves only the offered-goods form and
// opens the next task; typed goods entries survive a re-read.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import RequirementsTaskScreen from "./RequirementsTaskScreen.vue";
import { requirementsTask } from "./requirements.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor({ call, query = {} } = {}) {
	const route = ref({ path: `/tenders/${REF}/bid/requirements`, segments: ["tenders", REF, "bid", "requirements"], query });
	const go = vi.fn();
	return { call: call || vi.fn(async (m) => (m.endsWith("get_bid_task") ? requirementsTask() : { ok: true })), upload: vi.fn(async () => ({ ok: true })), go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal) {
	return mount(RequirementsTaskScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Requirements and supporting evidence", () => {
	it("opens the row an exact issue link names", async () => {
		const wrapper = mountWith(requirementsTask(), portalFor({ query: { item: "t6" } }));
		await nextTick();
		expect(wrapper.get('[data-testid="bds-response-drawer"]').text()).toContain(requirementsTask().technical.find((r) => r.key === "t6").label);
	});

	it("links every region with its state and lists the rows as the read words them", () => {
		const wrapper = mountWith(requirementsTask(), portalFor());
		expect(wrapper.findAll('[data-testid="bds-requirements-nav"] a').map((a) => a.attributes("href"))).toEqual(["#bds-region-goods", "#bds-region-technical", "#bds-region-warranty", "#bds-region-experience", "#bds-region-evidence"]);
		expect(wrapper.findAll('[data-testid="bds-technical-table"] tbody tr')).toHaveLength(11);
		expect(wrapper.get('[data-testid="bds-row-t6"]').text()).toContain("10 hours");
	});

	it("opens a requirement in the drawer and saves only its answer", async () => {
		const portal = portalFor();
		const wrapper = mountWith(requirementsTask(), portal);
		await wrapper.get('[data-testid="bds-row-t6"] button').trigger("click");
		await nextTick();
		const drawer = document.querySelector('[data-testid="bds-response-drawer"]');
		expect(drawer.querySelector('[role="dialog"]').getAttribute("aria-label")).toBe("Battery runtime");
		const input = drawer.querySelector("#bds-drawer-t6-v");
		input.value = "11 hours";
		input.dispatchEvent(new Event("input"));
		await nextTick();
		drawer.querySelector('[data-testid="bds-drawer-save"]').click();
		await flushPromises();
		expect([portal.call.mock.calls[0][1].task, JSON.parse(portal.call.mock.calls[0][1].values)]).toEqual(["requirements", { "t6-v": "11 hours" }]);
	});

	it("opens the row to fix from the attention notice", async () => {
		const wrapper = mountWith(requirementsTask("ATTENTION"), portalFor());
		expect(wrapper.get('[data-testid="bds-requirements-attention"]').text()).toContain("Fix 1 item");
		await wrapper.get('[data-testid="bds-requirements-attention"] button').trigger("click");
		await nextTick();
		expect(document.querySelector('[data-testid="bds-response-drawer"] [role="dialog"]').getAttribute("aria-label")).toBe("Product datasheet");
	});

	it("saves the offered goods and opens the next task; typed entries survive a re-read", async () => {
		const portal = portalFor();
		const wrapper = mountWith(requirementsTask(), portal);
		await wrapper.get("#bds-goods-g-model").setValue("ApexBook Pro 16");
		await wrapper.get('[data-testid="bds-row-t0"] button').trigger("click");
		await nextTick();
		document.querySelector('[data-testid="bds-response-drawer"]').dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
		await wrapper.get('[data-testid="bds-requirements-save"]').trigger("click");
		await flushPromises();
		expect(JSON.parse(portal.call.mock.calls[0][1].values)).toEqual({ "g-model": "ApexBook Pro 16" });
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/price`);
	});
});
