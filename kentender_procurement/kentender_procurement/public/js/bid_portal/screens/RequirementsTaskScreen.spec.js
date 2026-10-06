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
		expect(wrapper.findAll('[data-testid="bds-requirements-nav"] a.bds-section-link').map((a) => a.attributes("href"))).toEqual(["#bds-region-goods", "#bds-region-technical", "#bds-region-warranty", "#bds-region-experience", "#bds-region-evidence"]);
		expect(wrapper.findAll('[data-testid="bds-technical-table"] tbody tr')).toHaveLength(11);
		expect(wrapper.get('[data-testid="bds-row-t6"]').text()).toContain("10 hours");
	});

	it("opens with the bid's task order when the server sends it, and names where Save and continue leads", async () => {
		const task = requirementsTask();
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-stepper"]').exists()).toBe(false); // a read without a step draws none
		task.step = {
			number: 3, of: 5, label: "Requirements and supporting evidence", previous: { label: "Company and declarations", href: "/tenders/T/bid/company" }, next: { label: "Price", href: "/tenders/T/bid/price" },
			tasks: ["Tender documents", "Company and declarations", "Requirements", "Price", "Review and submit"].map((short, i) => ({ number: i + 1, key: short, label: short, short, status: "Complete", tone: "live", href: `/tenders/T/bid/${i}`, current: i === 2 })),
		};
		task.footer = { save_label: "Save and continue to Company and declarations", next_href: "/tenders/T/bid/company" };
		const stepped = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(stepped.get('[data-testid="bds-stepper-where"]').text()).toBe("Step 3 of 5");
		expect(stepped.get('[data-testid="bds-requirements-save"]').text()).toBe("Save and continue to Company and declarations");
	});

	it("keeps a way back to the top beside the region links, which stay in view while the page scrolls", async () => {
		const wrapper = mountWith(requirementsTask(), portalFor());
		const top = wrapper.get('[data-testid="bds-requirements-nav"] [data-testid="bds-section-top"]');
		expect([top.attributes("href"), top.text()]).toEqual(["#kt-portal-main", "↑ Top"]);
		// the region links come first and the Top link is last, so a screen reader reads the groups before it
		const links = wrapper.findAll('[data-testid="bds-requirements-nav"] a');
		expect(links.at(-1).attributes("data-testid")).toBe("bds-section-top");
		expect(links.slice(0, -1).every((a) => a.classes().includes("bds-section-link"))).toBe(true);
	});

	it("names the action on every row: Respond until it is started, Edit after, View when the bid cannot change", async () => {
		const task = requirementsTask();
		task.technical[0].status = "Not started";
		task.warranty[0].status = "Not started";
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const action = (key) => wrapper.get(`[data-testid="bds-row-${key}"] .btn-ghost`).text();
		expect([action(task.technical[0].key), action(task.technical[1].key), action(task.warranty[0].key), action(task.warranty[1].key)]).toEqual(["Respond", "Edit", "Respond", "Edit"]);
		expect(wrapper.findAll('[data-testid="bds-technical-table"] thead th').map((th) => th.text()).at(-1)).toBe("Action");
		task.bid = { ...task.bid, editable: false };
		const fixed = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(fixed.findAll("tbody .btn-ghost").map((b) => b.text()).filter((t) => t !== "View")).toEqual([]);
	});

	const TERMS = [
		{ key: "a1", label: "Quantity: Delivered quantities equal the authorised schedule", status: "Not started", tone: "draft", term: { check: "Quantity", passes_when: "Delivered quantities equal the authorised schedule", evidence: "Inspection record", applies_to: "All items" }, accepted: false, accept_status: "Not accepted yet", accept_tone: "draft", evidence_count: 0, evidence_names: [], evidence_rejected: false, fields: [] },
		{ key: "a2", label: "Functional test: Each device powers on", status: "Complete", tone: "live", term: { check: "Functional test", passes_when: "Each device powers on", evidence: "Test result", applies_to: "All items" }, accepted: true, accept_status: "Accepted", accept_tone: "live", evidence_count: 0, evidence_names: [], evidence_rejected: false, fields: [] },
	];

	it("presents acceptance as contract terms to confirm, set apart from the responses", async () => {
		const task = requirementsTask();
		task.acceptance = TERMS;
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const region = wrapper.get('[data-testid="bds-acceptance"]');
		expect(region.get("h2").text()).toBe("Acceptance terms — these become part of your contract");
		expect(region.get(".bds-terms-intro").text()).toContain("applied when the goods are delivered");
		expect(region.classes()).toContain("bds-terms");
		const rows = region.findAll("tbody tr");
		expect(rows[0].get(".bds-strong").text()).toBe("Quantity");
		expect(rows[0].get(".bds-muted").text()).toBe("Delivered quantities equal the authorised schedule");
		expect(rows[0].text()).toContain("Inspection record");
		expect(rows.map((tr) => tr.get(".kt-status").text())).toEqual(["Not accepted yet", "Accepted"]);
		expect(rows.map((tr) => tr.get(".btn-ghost").text())).toEqual(["Confirm", "Review"]);
		expect(region.text()).not.toContain("Respond");
		expect(region.text()).not.toContain("Not started");
		// read-only when the bid cannot change
		task.bid = { ...task.bid, editable: false };
		const fixed = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(fixed.findAll('[data-testid="bds-acceptance"] tbody .btn-ghost').map((b) => b.text())).toEqual(["View", "View"]);
		// narrow cards say the same
		globalThis.__narrow = true;
		const narrow = mountWith(requirementsTask() && { ...task, bid: { ...task.bid, editable: true } }, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const cards = narrow.get('[data-testid="bds-acceptance"]');
		expect(cards.text()).toContain("Not accepted yet");
		expect(cards.text()).toContain("Inspection record");
		expect(cards.text()).not.toContain("Respond");
	});

	it("keeps a requirement's name and its published words apart, and lines every table's columns up", async () => {
		const task = requirementsTask();
		task.warranty[0].label = "Warranty contact";
		task.warranty[0].requirement = "Supplier to provide escalation details.";
		task.acceptance = TERMS;
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const cell = wrapper.get(`[data-testid="bds-row-${task.warranty[0].key}"] td`);
		expect(cell.get(".bds-strong").text()).toBe("Warranty contact");
		expect(cell.get(".bds-muted").text()).toBe("Supplier to provide escalation details.");
		// the right-hand columns (Status, Action) share their edges across the response tables
		const widths = (testid) => wrapper.findAll(`[data-testid="${testid}"] col`).map((c) => parseFloat(c.attributes("style").match(/width:\s*([\d.]+)%/)[1]));
		const edge = (testid, n) => widths(testid).slice(-n).reduce((a, b) => a + b, 0);
		for (const t of ["bds-technical-table", "bds-warranty-table", "bds-acceptance-table", "bds-evidence-table"]) {
			expect(widths(t).reduce((a, b) => a + b, 0)).toBeCloseTo(100, 5);
			expect(wrapper.get(`[data-testid="${t}"]`).classes()).toContain("bds-fixed-table");
		}
		expect(["bds-technical-table", "bds-warranty-table", "bds-evidence-table"].map((t) => edge(t, 2))).toEqual([20, 20, 20]);
		// the acceptance terms are set apart in their own panel, with room for "Not accepted yet"
		expect(widths("bds-acceptance-table").slice(-2).reduce((a, b) => a + b, 0)).toBeGreaterThan(20);
	});

	it("shows the evidence table's File column as a paperclip and a count too, never the names", async () => {
		const task = requirementsTask();
		task.evidence[0].evidence_count = 2;
		task.evidence[0].evidence_names = ["WhatsApp Image 2026-10-01 at 11.19.37 PM (1).jpeg", "second.pdf"];
		task.evidence[0].file = "second.pdf";
		task.evidence[1].evidence_count = 0;
		task.evidence[1].evidence_names = [];
		task.evidence[1].file = "";
		task.evidence[1].file_status = "Missing";
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		const table = wrapper.get('[data-testid="bds-evidence-table"]');
		expect(table.text()).not.toContain("WhatsApp");
		expect(table.text()).not.toContain("second.pdf");
		expect(table.get(`[data-testid="bds-row-${task.evidence[0].key}"] .bds-attachment-count`).text()).toBe("2");
		expect(table.find(`[data-testid="bds-row-${task.evidence[1].key}"] [data-testid="bds-attachments"]`).exists()).toBe(false);
		globalThis.__narrow = true;
		const narrow = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(narrow.get('[data-testid="bds-evidence-cards"]').text()).not.toContain("WhatsApp");
		expect(narrow.get('[data-testid="bds-evidence-cards"] .bds-attachment-count').text()).toBe("2");
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
		const verbs = wrapper.findAll('[data-testid="bds-evidence-table"] tbody .btn-ghost').map((b) => b.text());
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

	it("does what its label says: Save stays on the page and re-reads when this is the only task left, then shows what is missing", async () => {
		const task = requirementsTask();
		task.footer = { save_label: "Save", next_href: `/tenders/${REF}/bid/requirements`, stays: true };
		const call = vi.fn(async () => task);
		const portal = portalFor({ call });
		const wrapper = mountWith(task, portal);
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-requirements-save"]').text()).toBe("Save");
		call.mockClear();
		await wrapper.get('[data-testid="bds-requirements-save"]').trigger("click");
		await flushPromises();
		expect(portal.go).not.toHaveBeenCalled();
		expect(call).toHaveBeenCalledTimes(1); // the re-read of the task, not a navigation
		expect(call.mock.calls[0][0]).toContain("get_bid_task");
	});

	it("goes where the label said when it was clicked, even if a re-read changes the footer meanwhile", async () => {
		const task = requirementsTask();
		task.footer = { save_label: "Save and continue to Price", next_href: `/tenders/${REF}/bid/price` };
		const portal = portalFor({ call: vi.fn(async (method) => (method.includes("save_bid_task") ? { ok: true } : { ...task, footer: { save_label: "Save", next_href: `/tenders/${REF}/bid/requirements`, stays: true } })) });
		const wrapper = mountWith(task, portal);
		await wrapper.get("#bds-goods-g-model").setValue("ApexBook Pro 16");
		await wrapper.get('[data-testid="bds-requirements-save"]').trigger("click");
		await flushPromises();
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/price`);
	});

	it("reads as fixed when the server says the bid cannot change: no Save and continue, rows open to View", async () => {
		const task = requirementsTask();
		task.bid = { ...task.bid, editable: false };
		const wrapper = mountWith(task, portalFor({ call: vi.fn(async () => task) }));
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-requirements-save"]').exists()).toBe(false);
		const labels = wrapper.findAll(".btn-ghost").map((b) => b.text());
		expect(labels.length).toBeGreaterThan(0);
		expect(labels.filter((l) => ["Edit", "Upload", "Replace"].includes(l))).toEqual([]);
	});
});
