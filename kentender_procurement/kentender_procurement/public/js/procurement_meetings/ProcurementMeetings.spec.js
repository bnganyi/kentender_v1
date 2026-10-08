// The Procurement meetings register page (OVS-CHG-001 v0.6 §11, §15: OVS-AC-012,
// OVS-AC-016; board views OVS-PRC-01 to 06). Mounted against a stubbed server so the
// page's own behaviour is proven: totals and rows, contributors, filters that follow
// the reader's own choices, Clear filters, the incomplete-totals state with Try again,
// the forbidden panel, the two empty states, and Show more.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";

import ProcurementMeetings from "./ProcurementMeetings.vue";

const DEPTS = [{ unit: "OU-A", name: "Digital Health" }, { unit: "OU-B", name: "Human Resources Management and Development" }];
const row = (o) => ({ proceeding: "PRC-1", type: "Bid opening", tender: "TND-MOH-2027-002", title: "Clinical training laptops", session: 1, state: "Finalized", held: true, date_label: "12 Jun 2027, 11:00 EAT",
	duration_minutes: 12, present: 4, department: "OU-A", department_name: "Digital Health", contributors: ["Human Resources Management and Development"], route: ["tenders", "TND-MOH-2027-002", "opening"], ...o });
const answer = (o = {}) => ({ rows: [row({}), row({ proceeding: "PRC-2", type: "Bid evaluation", session: 1, state: "Session ended", duration_minutes: 6, route: ["tenders", "TND-MOH-2027-002", "evaluation"] }),
	row({ proceeding: "PRC-3", type: "Bid evaluation", session: 2, state: "Session ended", duration_minutes: 75, present: 3, contributors: [], route: ["tenders", "TND-MOH-2027-002", "evaluation"] }),
	row({ proceeding: "PRC-4", tender: "TND-MOH-2027-009", title: "Staff training", type: "Bid opening", session: null, state: "Not held", held: false, date_label: "Scheduled 20 Jun 2027", duration_minutes: null, present: null,
		department: "OU-B", department_name: "Human Resources Management and Development", contributors: [] })],
	matched: 4, held_total: 3, totals: { by_type: { "Bid opening": 1, "Bid evaluation": 2 }, grouping: "Grouped by lead department",
		by_department: [{ department: "OU-A", department_name: "Digital Health", "Bid opening": 1, "Bid evaluation": 2, total: 3 }, { department: "OU-B", department_name: "Human Resources Management and Development", "Bid opening": 0, "Bid evaluation": 0, total: 0 }] },
	incomplete: false, incomplete_message: "", forbidden: false, filters: {}, options: { types: ["Bid opening", "Bid evaluation"], departments: DEPTS, states: ["Finalized", "Not held", "Session ended"] }, start: 0, limit: 50, ...o });

let calls;
let respond;
function stub() {
	calls = [];
	globalThis.frappe = Object.assign(globalThis.frappe || {}, {
		call: vi.fn(async ({ args, type }) => { if (type !== "GET") throw Object.assign(new Error("Not permitted"), { status: 403 }); calls.push(args); return { message: await respond(args) }; }),
		set_route: vi.fn(), session: { user: "amina.hassan@moh.example.test" },
	});
	globalThis.__ = (s) => s;
	globalThis.kentender_core = Object.assign(globalThis.kentender_core || {}, { industry: { ...(globalThis.kentender_core?.industry || {}), mountPageRail: () => ({ unmount() {}, update() {} }) } });
}
async function page() {
	const w = mount(ProcurementMeetings, { attachTo: document.body, global: { config: { globalProperties: { __: (s) => s, frappe: globalThis.frappe } } } });
	await flushPromises();
	return w;
}

beforeEach(() => { vi.useFakeTimers({ toFake: ["setTimeout", "clearTimeout"] }); stub(); respond = async () => answer(); });
afterEach(() => { vi.useRealTimers(); });

describe("Procurement meetings", () => {
	it("shows the totals by type and by lead department, and one row per meeting", async () => {
		const w = await page();
		expect(w.find('[data-testid="pmt-title"]').text()).toBe("Procurement meetings");
		expect(w.find('[data-testid="pmt-totals"]').text()).toContain("Grouped by lead department");
		expect(w.find('[data-testid="pmt-held-total"]').text()).toBe("3");
		const byDept = w.findAll('[data-testid="pmt-by-department"] tbody tr').map((r) => r.findAll("td").map((c) => c.text()));
		expect(byDept).toEqual([["Digital Health", "1", "2", "3"], ["Human Resources Management and Development", "0", "0", "0"]]);
		expect(w.findAll('[data-testid="pmt-rows"] tbody tr')).toHaveLength(4);
		expect(w.find('[data-testid="pmt-count"]').text()).toBe("4 meetings");
		w.unmount();
	});
	it("names a contributing department under the lead, and shows a Not held meeting without a session or a count", async () => {
		const w = await page();
		const rows = w.findAll('[data-testid="pmt-rows"] tbody tr');
		expect(rows[0].text()).toContain("Contributor: Human Resources Management and Development");
		const notHeld = rows[3].text().replace(/\s+/g, " ");
		expect(notHeld).toContain("Scheduled 20 Jun 2027");
		expect(notHeld).toContain("Not held");
		expect(notHeld).not.toMatch(/\bmin\b/);
		expect(rows[2].text()).toContain("1 h 15 min");
		w.unmount();
	});
	it("a row never shows a subject, a bidder or a bid count", async () => {
		const w = await page();
		const text = w.text();
		for (const word of ["subject", "Afya", "bids opened", "finding"]) expect(text.toLowerCase()).not.toContain(word.toLowerCase());
		w.unmount();
	});
	it("opens the meeting's own record from View record", async () => {
		const w = await page();
		await w.findAll('[data-testid="pmt-rows"] tbody tr')[1].find("a").trigger("click");
		expect(frappe.set_route).toHaveBeenCalledWith("tenders", "TND-MOH-2027-002", "evaluation");
		w.unmount();
	});
	it("offers no View record link for a row whose record this reader cannot open", async () => {
		// KT-ACCESS-REV-001 AR-07: the row is meeting facts; the opening record applies its own rule.
		const full = answer();
		full.rows[0] = { ...full.rows[0], record_readable: false };
		respond = async () => full;
		const w = await page();
		const rows = w.findAll('[data-testid="pmt-rows"] tbody tr');
		expect(rows).toHaveLength(4);
		expect(rows[0].find("a").exists()).toBe(false);
		expect(rows[0].find('[data-testid="pmt-no-record"]').exists()).toBe(true);
		expect(rows[1].find("a").exists()).toBe(true); // the rest still open
	});

	it("sends the reader's own filter choices and offers Clear filters only while filtered", async () => {
		const w = await page();
		expect(w.find('[data-testid="pmt-clear"]').exists()).toBe(false);
		await w.find("#pmt-type").setValue("Bid evaluation");
		await w.find("#pmt-q").setValue("TND-MOH-2027-002");
		vi.advanceTimersByTime(300);
		await flushPromises();
		expect(calls.at(-1)).toMatchObject({ type: "Bid evaluation", query: "TND-MOH-2027-002", start: 0, limit: 10 });
		expect(w.find("#pmt-type").element.value).toBe("Bid evaluation"); // bound to the reader's choice, not the server's echo
		expect(w.find('[data-testid="pmt-clear"]').exists()).toBe(true);
		await w.find('[data-testid="pmt-clear"]').trigger("click");
		vi.advanceTimersByTime(300);
		await flushPromises();
		expect(calls.at(-1)).toMatchObject({ type: "", query: "", department: "", state: "", date_from: "", date_to: "" });
		expect(w.find('[data-testid="pmt-clear"]').exists()).toBe(false);
		w.unmount();
	});
	it("says totals are incomplete, never as the whole, and offers Try again", async () => {
		respond = async () => answer({ incomplete: true, incomplete_message: "Some meeting records could not be loaded. Totals are incomplete." });
		const w = await page();
		expect(w.find('[data-testid="pmt-incomplete"]').text()).toContain("Some meeting records could not be loaded. Totals are incomplete.");
		const before = calls.length;
		await w.find('[data-testid="pmt-incomplete"] button').trigger("click");
		await flushPromises();
		expect(calls.length).toBe(before + 1);
		w.unmount();
	});
	it("gives a reader with no responsibility the forbidden panel and no data", async () => {
		respond = async () => answer({ forbidden: true, rows: [], matched: 0, held_total: 0 });
		const w = await page();
		expect(w.find('[data-testid="pmt-forbidden"]').text()).toContain("You do not have access to Procurement meetings.");
		expect(w.find('[data-testid="pmt-rows"]').exists()).toBe(false);
		w.unmount();
	});
	it("tells no records yet apart from no matches", async () => {
		respond = async () => answer({ rows: [], matched: 0, held_total: 0 });
		const w = await page();
		expect(w.find('[data-testid="pmt-empty"]').text()).toContain("No procurement meetings have been recorded yet.");
		await w.find("#pmt-q").setValue("nothing");
		vi.advanceTimersByTime(300);
		await flushPromises();
		expect(w.find('[data-testid="pmt-empty"]').text()).toContain("No meetings match these filters.");
		w.unmount();
	});
	it("pages on the server: the page asks for its own slice and the total stays the matched count", async () => {
		respond = async (a) => answer({ matched: 120, held_total: 90, rows: answer().rows.slice(0, 2) });
		const w = await page();
		expect(calls.at(-1)).toMatchObject({ limit: 10, start: 0 });
		expect(w.find('[data-testid="kt-pager-count"]').text()).toBe("Showing 1–10 of 120 meetings");
		await w.find('[data-testid="kt-pager-page-3"]').trigger("click");
		await flushPromises();
		expect(calls.at(-1)).toMatchObject({ limit: 10, start: 20 });
		await w.find('[data-testid="kt-pager-size"]').setValue("50");
		await flushPromises();
		expect(calls.at(-1)).toMatchObject({ limit: 50, start: 0 });
		expect(w.find('[data-testid="pmt-held-total"]').text()).toBe("90");
		w.unmount();
	});
	it("keeps the old answer on screen while a later load runs, with a failure on the first load shown plainly", async () => {
		const w = await page();
		respond = async () => { throw Object.assign(new Error("x"), { httpStatus: 500 }); };
		await w.find("#pmt-q").setValue("x");
		vi.advanceTimersByTime(300);
		await flushPromises();
		expect(w.find('[data-testid="pmt-rows"]').exists()).toBe(true); // revalidate in place
		expect(w.find('[data-testid="pmt-stale"]').text()).toContain("What you see may be out of date.");
		respond = async () => answer();
		await w.find('[data-testid="pmt-stale"] button').trigger("click");
		await flushPromises();
		expect(w.find('[data-testid="pmt-stale"]').exists()).toBe(false);
		w.unmount();
		respond = async () => { throw Object.assign(new Error("x"), { httpStatus: 500 }); };
		const failed = await page();
		expect(failed.find('[data-testid="pmt-failure"]').text()).toContain("We could not load Procurement meetings.");
		failed.unmount();
	});
});
