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

	it("names the action on every row: Respond until it is started, Edit after, View when the bid cannot change", async () => {
		const task = requirementsTask();
		task.technical[0].status = "Not started";
		task.warranty[0].status = "Not started";
		task.acceptance = [{ key: "a1", label: "Quantity: Delivered quantities equal the authorised schedule", status: "Not started", tone: "draft" }, { key: "a2", label: "Functional test", status: "Complete", tone: "live" }];
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const action = (key) => wrapper.get(`[data-testid="bds-row-${key}"] .bds-link-button`).text();
		expect([action(task.technical[0].key), action(task.technical[1].key), action(task.warranty[0].key), action(task.warranty[1].key)]).toEqual(["Respond", "Edit", "Respond", "Edit"]);
		expect(wrapper.findAll('[data-testid="bds-technical-table"] thead th').map((th) => th.text()).at(-1)).toBe("Action");
		expect(wrapper.findAll('[data-testid="bds-acceptance-table"] tbody tr').map((tr) => tr.get(".bds-link-button").text())).toEqual(["Respond", "Edit"]);
		task.bid = { ...task.bid, editable: false };
		const fixed = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(fixed.findAll("tbody .bds-link-button").map((b) => b.text()).filter((t) => t !== "View")).toEqual([]);
	});

	it("keeps a requirement's name and its published words apart, and lines every table's columns up", async () => {
		const task = requirementsTask();
		task.warranty[0].label = "Warranty contact";
		task.warranty[0].requirement = "Supplier to provide escalation details.";
		task.acceptance = [{ key: "a1", label: "Quantity: Delivered quantities equal the authorised schedule", status: "Not started", tone: "draft" }];
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const cell = wrapper.get(`[data-testid="bds-row-${task.warranty[0].key}"] td`);
		expect(cell.get(".bds-strong").text()).toBe("Warranty contact");
		expect(cell.get(".bds-muted").text()).toBe("Supplier to provide escalation details.");
		// the right-hand columns (Status, Action) share their edges across every table
		const widths = (testid) => wrapper.findAll(`[data-testid="${testid}"] col`).map((c) => parseFloat(c.attributes("style").match(/width:\s*([\d.]+)%/)[1]));
		const edge = (testid, n) => widths(testid).slice(-n).reduce((a, b) => a + b, 0);
		for (const t of ["bds-technical-table", "bds-warranty-table", "bds-acceptance-table", "bds-evidence-table"]) {
			expect(widths(t).reduce((a, b) => a + b, 0)).toBeCloseTo(100, 5);
			expect(wrapper.get(`[data-testid="${t}"]`).classes()).toContain("bds-fixed-table");
		}
		expect(["bds-technical-table", "bds-warranty-table", "bds-acceptance-table", "bds-evidence-table"].map((t) => edge(t, 2))).toEqual([20, 20, 20, 20]);
	});

	it("shows how many files each row holds, not their names, and names the evidence table's action for what it opens", async () => {
		const task = requirementsTask();
		task.technical[0].evidence_count = 3;
		task.technical[0].evidence_names = ["WhatsApp Image 2026-10-01 at 11.19.37 PM (1).jpeg", "b.pdf", "c.pdf"];
		task.technical[1].evidence_count = 0;
		task.technical[1].evidence_names = [];
		task.technical[1].evidence = "—";
		task.evidence[0].file = "";
		task.evidence[0].file_status = "Missing";
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const chip = wrapper.get(`[data-testid="bds-row-${task.technical[0].key}"] [data-testid="bds-attachments"]`);
		expect(chip.get(".bds-attachment-count").text()).toBe("3");
		expect(wrapper.get('[data-testid="bds-technical-table"]').text()).not.toContain("WhatsApp");
		expect(wrapper.find(`[data-testid="bds-row-${task.technical[1].key}"] [data-testid="bds-attachments"]`).exists()).toBe(false);
		// the evidence table's button opens the files; Replace belongs to each file inside, so the button never says it
		const verbs = wrapper.findAll('[data-testid="bds-evidence-table"] tbody .bds-link-button').map((b) => b.text());
		expect(verbs[0]).toBe("Upload");
		expect(verbs.slice(1).every((v) => v === "Edit")).toBe(true);
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

	it("reads as fixed when the server says the bid cannot change: no Save and continue, rows open to View", async () => {
		const task = requirementsTask();
		task.bid = { ...task.bid, editable: false };
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-requirements-save"]').exists()).toBe(false);
		const labels = wrapper.findAll(".bds-link-button").map((b) => b.text());
		expect(labels.length).toBeGreaterThan(0);
		expect(labels.filter((l) => ["Edit", "Upload", "Replace"].includes(l))).toEqual([]);
	});
});
