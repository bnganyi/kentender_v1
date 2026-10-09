// ANL-CHG-001 v0.8 plan Phase 5 — the Analytics page against the 20 golden payloads (fixtures/ANL-DES-*.json),
// each exactly what `get_procurement_analytics` returns for that board. The page makes no phrase of its own, so
// every string asserted below is one the payload carries; the behaviour tests cover the URL contract of
// docs/mvp-1-r1/19_analytics/reconciliation/route_spike.md (tab in the path, filters in location.search, search
// and cursor never in the URL, Back and Forward re-read the address, never frappe.route_options).
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./data/analyticsApi.js", () => ({ analyticsApi: { load: vi.fn(), access: vi.fn() } }));

import Analytics from "./Analytics.vue";
import { analyticsApi } from "./data/analyticsApi.js";

const modules = import.meta.glob("./fixtures/ANL-DES-*.json", { eager: true, import: "default" });
const FX = {};
for (const [path, payload] of Object.entries(modules)) FX[path.match(/ANL-DES-([0-9A-Z]+)\.json$/)[1]] = payload;
const clone = (value) => JSON.parse(JSON.stringify(value));

// ----- the bench runtime the page leans on ---------------------------------------------------------------
const routeRef = ref(["analytics"]);
const epochRef = ref(0);
const mounted = [];

function installGlobals() {
	routeRef.value = ["analytics"];
	epochRef.value = 0;
	globalThis.kentender_core = {
		desk_page: {
			useRoute: () => ({ route: routeRef, epoch: epochRef, go() {}, isShown: () => true }),
			createSequenceGuard() {
				let token = 0;
				return { next: () => ++token, isCurrent: (candidate) => candidate === token };
			},
			createScreenCache() {
				const store = new Map();
				return { get: (k) => store.get(k), has: (k) => store.has(k), set: (k, v) => store.set(k, v), remove: (k) => store.delete(k), clear: () => store.clear() };
			},
		},
	};
	globalThis.frappe.set_route = vi.fn();
	// Frappe's own route_options keeps stale keys across Back and Forward (route_spike.md): the page must never read them.
	globalThis.frappe.route_options = { fy: "STALE-FROM-ROUTE-OPTIONS", dept: "STALE", state: "stale" };
	globalThis.frappe.router = {
		route: vi.fn(() => {
			const parts = window.location.pathname.split("/").filter(Boolean).slice(1);
			routeRef.value = parts.length ? parts : ["analytics"];
		}),
	};
}

function setUrl(path) {
	window.history.pushState(null, "", path);
}

function mountPage() {
	const wrapper = mount(Analytics, { attachTo: document.body, global: { mocks: { __: globalThis.__, frappe: globalThis.frappe } } });
	mounted.push(wrapper);
	return wrapper;
}

async function open(fixtureId, url, payload) {
	if (url) setUrl(url);
	analyticsApi.load.mockResolvedValue(payload || clone(FX[fixtureId]));
	const wrapper = mountPage();
	await flushPromises();
	return wrapper;
}

// The visible text, one space between pieces; the chart tables for assistive technology are left out.
function textOf(node) {
	const parts = [];
	const walk = (n) => {
		if (n.nodeType === 3) {
			const s = n.textContent.trim();
			if (s) parts.push(s);
		} else if (n.nodeType === 1 && !(n.classList && n.classList.contains("sr-only"))) n.childNodes.forEach(walk);
	};
	walk(node);
	return parts.join(" ").replace(/\s+/g, " ").trim();
}
const text = (target) => textOf(target.element || target);
const lastCall = () => analyticsApi.load.mock.calls[analyticsApi.load.mock.calls.length - 1][0];
const tick = () => new Promise((resolve) => setTimeout(resolve, 25));

beforeEach(() => {
	document.body.innerHTML = "";
	vi.clearAllMocks();
	installGlobals();
	setUrl("/desk/analytics");
});
afterEach(() => {
	while (mounted.length) mounted.pop().unmount();
});

// A board's own URL: its tab as a path segment, its applied filters as the query (ANL §9.1).
function boardUrl(payload) {
	const f = payload.filters;
	const query = new URLSearchParams();
	if (f.fy) query.set("fy", f.fy);
	if (f.dept) query.set("dept", f.dept);
	if (f.state) query.set("state", f.state);
	const qs = query.toString();
	return "/desk/analytics" + (payload.tab && payload.tab !== "overview" ? "/" + payload.tab : "") + (qs ? "?" + qs : "");
}

// =============================================================================================================
describe("every golden payload mounts", () => {
	for (const id of Object.keys(FX)) {
		it("ANL-DES-" + id + " renders its title and draws no error", async () => {
			const payload = FX[id];
			const wrapper = await open(id, boardUrl(payload));
			// A denied page is the shared access state: no page title above it.
			if (id === "31H") expect(wrapper.get('[data-testid="kt-anl-denied"] h2').text()).toBe("You do not have access to Analytics");
			else expect(wrapper.get('[data-testid="kt-anl-title"]').text()).toBe("Procurement Analytics");
			expect(wrapper.find('[data-testid="kt-anl-loading"]').exists()).toBe(false);
			if (payload.verdict === "ok" && !payload.empty) expect(wrapper.get('[data-testid="kt-anl-updated"]').text()).toBe(payload.updated);
			if (payload.verdict === "ok") expect(wrapper.find('[data-testid="kt-anl-tabs"] input:checked').element.value).toBe(payload.tab);
		});
	}
});

// =============================================================================================================
describe("ANL-DES-21 Charles, Overview", () => {
	it("shows the header, six tabs with Overview selected and the filter row", async () => {
		const wrapper = await open("21");
		expect(wrapper.get('[data-testid="kt-anl-header"]').text()).toContain("See where procurement work stands, how long key steps take and how much planned value is covered.");
		expect(wrapper.get('[data-testid="kt-anl-updated"]').text()).toBe("Updated 18 June 2027, 10:00 EAT");
		expect(wrapper.get('[data-testid="kt-anl-scope"]').text()).toBe("All departments");
		expect(wrapper.findAll(".kt-tab").map((t) => t.text())).toEqual(["Overview", "Needs", "Departmental planning", "Annual planning", "Requisitions", "Tender proceedings"]);
		expect(wrapper.get('.kt-tab input:checked').element.value).toBe("overview");
		expect(wrapper.get('[data-testid="kt-anl-fy"]').findAll("option").map((o) => o.text())).toEqual(["All years", "FY 2027/28"]);
		expect(wrapper.get('[data-testid="kt-anl-dept"]').findAll("option").map((o) => o.text())).toEqual(["All departments", "Digital Health", "Human Resources Management and Development"]);
		expect(wrapper.get('[data-testid="kt-anl-apply"]').text()).toBe("Apply filters");
		expect(wrapper.get('[data-testid="kt-anl-clear-filters"]').text()).toBe("Clear filters");
	});

	it("shows the five summary columns in order with their unit headline, bar legend, outstanding line and link", async () => {
		const wrapper = await open("21");
		const columns = wrapper.findAll('[data-testid^="kt-anl-strip-"]').filter((c) => c.classes().includes("kt-kpi-card"));
		expect(columns.map((c) => text(c))).toEqual([
			"Needs 2 Needs Accepted for planning 2 No outstanding matters recorded View Needs",
			"Departmental planning 2 departmental plans Accepted 2 No outstanding matters recorded View departmental planning",
			"Annual planning 7 Plan items in the Active Plan Fully covered 5 Partly covered 1 Not covered 1 No outstanding matters recorded View annual planning",
			"Requisitions 7 Requisitions Submitted to Procurement 1 Authorised 6 1 outstanding matter View Requisitions",
			"Tender proceedings 6 Tenders Preparation 1 Open 1 Evaluation 1 Award 2 Closed 1 4 outstanding matters View Tender proceedings",
		]);
		expect(wrapper.get('[data-testid="kt-anl-strip-note"]').text()).toBe("These counts describe different records and are not added together.");
	});

	it("draws Partly covered with the board's family-2 swatch and Closed with the board's cat-5 (tones the charts do not know)", async () => {
		const wrapper = await open("21");
		const annual = wrapper.get('[data-testid="kt-anl-strip-annual_planning"]');
		expect(annual.findAll(".kt-anl-legend > span").map((s) => s.classes().filter((c) => c.startsWith("is-")))).toEqual([["is-pair-strong"], ["is-family-2"], ["is-pair-tint"]]);
		const tender = wrapper.get('[data-testid="kt-anl-strip-tender_proceedings"]');
		expect(tender.findAll(".kt-anl-legend > span").map((s) => s.classes().filter((c) => c.startsWith("is-"))[0])).toEqual(["is-cat-1", "is-cat-2", "is-cat-3", "is-cat-4", "is-cat-5"]);
	});

	it("shows Outstanding matters by waiting time with the four-band legend, the two rows and the quiet sentence", async () => {
		const wrapper = await open("21");
		const region = wrapper.get('[data-testid="kt-anl-waiting"]');
		expect(text(region)).toBe(
			"Outstanding matters by waiting time 0–7 days 8–30 days 31–90 days Over 90 days Requisitions 1 Tender proceedings 3 1 " +
				"Needs, departmental planning and annual planning: no outstanding matters recorded. Days since each matter reached its current holder.",
		);
		expect(region.find(".kt-anl-segrows").classes()).toContain("is-bands");
	});

	it("shows Plan coverage: 81%, the planned value, both segments, the item sentence and the link", async () => {
		const wrapper = await open("21");
		const region = wrapper.get('[data-testid="kt-anl-coverage"]');
		expect(text(region)).toBe(
			"Plan coverage 81% of planned value is covered by authorised requisitions Planned value KES 68,500,000 in the Active Plan " +
				"Covered by authorised requisitions KES 55,500,000 Not yet covered KES 13,000,000 5 Plan items fully covered, 1 partly covered, 1 not covered. View annual planning",
		);
		expect(region.get(".kt-result-value").text()).toBe("81%");
	});

	it("shows Time between key steps: five rows with Completed, Median, Shortest and Longest on a 0 to 60 axis", async () => {
		const wrapper = await open("21");
		const region = wrapper.get('[data-testid="kt-anl-steps"]');
		const rows = region.findAll(".kt-anl-range-row:not(.is-head):not(.is-axis)");
		expect(rows.map((r) => text(r))).toEqual([
			"Requisition submitted to authorised 6 8.5 days 6 days 14 days",
			"Requisition authorised to Tender started 6 3.5 days 1 day 5 days",
			"Tender started to published 5 26 days 21 days 56 days",
			"Bid opening complete to evaluation report sent 2 32.5 days 28 days 37 days",
			"Evaluation report sent to AO decision recorded 1 13 days 13 days 13 days",
		]);
		expect(text(region.find(".kt-anl-range-row.is-head"))).toBe("Step Completed Median Shortest Longest");
		expect(text(region.find(".kt-anl-range-axis"))).toBe("0 10 20 30 40 50 60");
		expect(text(region)).toContain("Calendar days, last 12 months.");
		expect(text(region)).toContain("Median Shortest to longest");
	});

	it("shows the quiet funding line when All years is selected, and no register on Overview", async () => {
		const wrapper = await open("21");
		expect(wrapper.get('[data-testid="kt-anl-funding-message"]').text()).toBe("Choose a financial year to see its funding position.");
		expect(wrapper.find('[data-testid="kt-anl-register"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-funding"]').exists()).toBe(false);
	});

	it("keeps How these figures are counted collapsed, and expands it on its button with aria-expanded", async () => {
		const wrapper = await open("21");
		const toggle = wrapper.get('[data-testid="kt-anl-definitions-toggle"]');
		expect(toggle.text()).toBe("How these figures are counted");
		expect(toggle.attributes("aria-expanded")).toBe("false");
		expect(wrapper.find('[data-testid="kt-anl-definitions-body"]').exists()).toBe(false);
		await toggle.trigger("click");
		expect(toggle.attributes("aria-expanded")).toBe("true");
		const body = wrapper.get('[data-testid="kt-anl-definitions-body"]').text();
		expect(body).toBe(FX["21"].definitions);
		expect(body.startsWith("Each area counts its own permitted records once.")).toBe(true);
		expect(body.endsWith("All area reads completed at 10:00 EAT.")).toBe(true);
		await toggle.trigger("click");
		expect(toggle.attributes("aria-expanded")).toBe("false");
		expect(wrapper.find('[data-testid="kt-anl-definitions-body"]').exists()).toBe(false);
	});

	it("draws the spot illustration on none of the ordinary boards", async () => {
		const wrapper = await open("21");
		expect(wrapper.find(".kt-spot").exists()).toBe(false);
	});

	it("carries the page root classes and no register or search on Overview", async () => {
		const wrapper = await open("21");
		expect(wrapper.get('[data-testid="kt-anl-root"]').classes()).toEqual(expect.arrayContaining(["kt-industry", "kt-analytics"]));
		expect(wrapper.find('[data-testid="kt-anl-search"]').exists()).toBe(false);
	});
});

// =============================================================================================================
describe("ANL-DES-22 and 23, Tender proceedings", () => {
	it("22: shows 6 Tenders, four outstanding rows in the v0.8 form, both charts, four step rows and the register", async () => {
		const wrapper = await open("22", boardUrl(FX["22"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("6 Tenders");
		const rows = wrapper.findAll('[data-testid="kt-anl-orow"]');
		expect(rows.map((r) => text(r))).toEqual([
			"Supply of IT peripherals State the warranty period required from suppliers. Awaiting correction by Brian Wafula. Waiting 2 days since 16 June, 09:00",
			"Supply of office desks Automatic checks complete; committee review outstanding. Grace Wambui chairs the appointed committee. Waiting 15 days since 3 June, 10:00",
			"Supply of printers Awaiting professional opinion by Charles Mutiso. Waiting 2 days since 16 June, 14:07",
			"Supply of monitors Award decision recorded. Required bidder notices are awaiting delivery. Waiting 1 day since 17 June, 11:00",
		]);
		expect(rows[0].get("strong").text()).toBe("Supply of IT peripherals");
		expect(rows[0].get(".kt-ap-badge").text()).toBe("Waiting 2 days");
		const stages = wrapper.get(".kt-anl-hbars");
		expect(text(stages)).toBe(
			"Authorised requisition value Tender preparation and publication 1 KES 6,500,000 Open for bids 1 KES 8,000,000 Evaluation 1 KES 3,500,000 Award 2 KES 12,500,000 Closed 1 KES 25,000,000",
		);
		expect(text(wrapper.get('[data-testid="kt-anl-charts"]'))).toContain("1 AO award decision recorded. Award amount KES 7,185,000.");
		expect(text(wrapper.get('[data-testid="kt-anl-charts"]'))).toContain("Published Cancelled AO award decisions");
		const published = wrapper.findAll(".kt-anl-vbars-bar").map((b) => b.get("b").text());
		expect(published).toEqual(["4", "1", "1", "1"]);
		expect(wrapper.findAll(".kt-anl-vbars-slot")).toHaveLength(12);
		expect(text(wrapper.get(".kt-anl-vbars-axis"))).toBe("Jul 2026 Aug Sep Oct Nov Dec Jan 2027 Feb Mar Apr May Jun (to date)");
		expect(wrapper.get('[data-testid="kt-anl-steps"]').findAll(".kt-anl-range-row:not(.is-head):not(.is-axis)").map((r) => text(r).split(" ").slice(-7).join(" "))).toHaveLength(4);
	});

	it("22: the register has the five columns, six rows, secondary references and enabled View record links", async () => {
		const wrapper = await open("22", boardUrl(FX["22"]));
		const table = wrapper.get('[data-testid="kt-anl-table"]');
		expect(table.findAll("th").map((t) => t.text())).toEqual(["Tender", "Current position", "Authorised requisition value", "Recorded AO outcome", "Action"]);
		const rows = table.findAll('[data-testid="kt-anl-row"]');
		expect(rows).toHaveLength(6);
		expect(text(rows[0])).toBe("Supply of IT peripherals TND-MOH-2027-041 Tender preparation — warranty requirement returned for correction KES 6,500,000 No AO award decision recorded View record");
		expect(text(rows[4])).toBe("Supply of monitors TND-MOH-2027-045 Award — required bidder notices awaiting delivery KES 7,500,000 Award decision recorded 17 June 2027, 11:00 EAT Award amount KES 7,185,000 View record");
		expect(text(rows[5])).toContain("Cancellation recorded 16 June 2027, 12:00 EAT");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 6 of 6 Tenders");
		expect(wrapper.get('[data-testid="kt-anl-search"]').attributes("placeholder")).toBe("Search Tender or reference");
		expect(wrapper.get('[data-testid="kt-anl-search"]').element.value).toBe("");
		expect(wrapper.get('[data-testid="kt-anl-state"]').findAll("option").map((o) => o.text())).toEqual(["All stages", "Tender preparation and publication", "Open for bids", "Evaluation", "Award", "Closed"]);
		expect(wrapper.find('[data-testid="kt-anl-next"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-scope-label"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-clear-register"]').exists()).toBe(false);
	});

	it("23: the Award bar is selected with the accent, the select shows Award, Clear stage filter and the whole-area label", async () => {
		const wrapper = await open("23", boardUrl(FX["23"]));
		expect(boardUrl(FX["23"])).toBe("/desk/analytics/tender-proceedings?state=award");
		expect(wrapper.get(".kt-anl-hbars-label.is-selected").text()).toBe("Award");
		expect(wrapper.findAll(".kt-anl-hbars-track > span.is-selected")).toHaveLength(1);
		expect(wrapper.get('[data-testid="kt-anl-state"]').element.value).toBe("award");
		expect(wrapper.get('[data-testid="kt-anl-clear-register"]').text()).toBe("Clear stage filter");
		expect(wrapper.get('[data-testid="kt-anl-scope-label"]').text()).toBe("All 6 Tenders in this area");
		expect(wrapper.findAll('[data-testid="kt-anl-row"]')).toHaveLength(2);
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 2 of 2 matching Tenders");
		// the chart and the area result are still the whole area
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("6 Tenders");
	});

	it("23: the Clear stage filter pushes the tab route without state, and a click on a stage bar pushes that state", async () => {
		const wrapper = await open("23", boardUrl(FX["23"]));
		const push = vi.spyOn(window.history, "pushState");
		await wrapper.get('[data-testid="kt-anl-clear-register"]').trigger("click");
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/tender-proceedings");
		expect(push).toHaveBeenCalledTimes(1);
		await wrapper.findAll(".kt-anl-hbars-label").find((l) => l.text() === "Evaluation").trigger("click");
		expect(window.location.search).toBe("?state=evaluation");
		expect(push).toHaveBeenCalledTimes(2);
		expect(lastCall()).toMatchObject({ tab: "tender-proceedings", state: "evaluation" });
	});

	it("31A: no search match shows the sentence, Clear search, the zero footer and keeps the whole-area charts", async () => {
		const wrapper = await open("31A", boardUrl(FX["31A"]));
		expect(text(wrapper.get('[data-testid="kt-anl-nomatch"]'))).toBe("No records match these filters. Clear search");
		expect(wrapper.get('[data-testid="kt-anl-clear-register"]').text()).toBe("Clear search");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("0 matching Tenders");
		expect(wrapper.get('[data-testid="kt-anl-scope-label"]').text()).toBe("All 6 Tenders in this area");
		expect(wrapper.find('[data-testid="kt-anl-table"]').exists()).toBe(false);
		expect(wrapper.findAll('[data-testid="kt-anl-orow"]')).toHaveLength(4);
	});

	it("31F: one Tender's stage unavailable shows Status unavailable in the chart and the register, and the neutral board colour", async () => {
		const wrapper = await open("31F", boardUrl(FX["31F"]));
		expect(text(wrapper.get(".kt-anl-hbars"))).toContain("Status unavailable 1 KES 5,000,000");
		const row = wrapper.findAll('[data-testid="kt-anl-row"]')[3];
		expect(text(row)).toBe("Supply of printers TND-MOH-2027-044 Status unavailable KES 5,000,000 Could not be loaded View record");
		expect(wrapper.get('[data-testid="kt-anl-state"]').findAll("option").map((o) => o.text())).toContain("Status unavailable");
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("6 Tenders");
		const unavailable = wrapper.findAll(".kt-anl-hbars-track > span").pop();
		expect(unavailable.classes().some((c) => c.startsWith("is-cat"))).toBe(false);
	});

	it("30: Peter's department view shows four Tenders and the contributor line", async () => {
		const wrapper = await open("30", boardUrl(FX["30"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("4 Tenders");
		expect(wrapper.get('[data-testid="kt-anl-scope"]').text()).toBe("Human Resources Management and Development");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 4 of 4 Tenders");
		expect(text(wrapper.findAll('[data-testid="kt-anl-row"]')[0])).toContain("Human Resources Management and Development share of KES 6,500,000");
	});
});

// =============================================================================================================
describe("Requisitions, planning and Needs tabs", () => {
	it("24: Requisitions shows 7 Requisitions, one outstanding row, state and monthly charts and the register", async () => {
		const wrapper = await open("24", boardUrl(FX["24"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("7 Requisitions");
		expect(wrapper.findAll('[data-testid="kt-anl-orow"]').map((r) => text(r))).toEqual([
			"Clinic equipment requisition Awaiting authorisation by Charles Mutiso. Waiting 2 days since 16 June, 11:00",
		]);
		expect(text(wrapper.get(".kt-anl-hbars"))).toBe("Requisition value Submitted to Procurement 1 KES 12,000,000 requested Authorised 6 KES 55,500,000 authorised");
		expect(text(wrapper.get('[data-testid="kt-anl-charts"]'))).toContain("Requisitions by current state");
		expect(wrapper.get('[data-testid="kt-anl-table"]').findAll("th").map((t) => t.text())).toEqual(["Requisition", "Current position", "Requisition value", "Tender relationship", "Action"]);
		const rows = wrapper.findAll('[data-testid="kt-anl-row"]');
		expect(rows).toHaveLength(7);
		expect(text(rows[1])).toBe("IT peripherals requisition Authorised KES 6,500,000 authorised TND-MOH-2027-041 created View record");
		expect(text(rows[0])).toContain("No Tender created");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 7 of 7 Requisitions");
		expect(wrapper.get('[data-testid="kt-anl-state"]').findAll("option").map((o) => o.text())).toEqual(["All states", "Submitted to Procurement", "Authorised"]);
		expect(wrapper.get('[data-testid="kt-anl-steps"]').findAll(".kt-anl-range-row:not(.is-head):not(.is-axis)")).toHaveLength(2);
	});

	it("25: Annual planning shows the area result, source, result figures, the three charts and the register", async () => {
		const wrapper = await open("25", boardUrl(FX["25"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("7 Plan items in the Active Plan No outstanding matters recorded in this selection. Ministry of Health Annual Procurement Plan, Active Version 1");
		expect(wrapper.findAll('[data-testid="kt-anl-figures"] .kt-kpi-card').map((c) => text(c))).toEqual([
			"Planned value KES 68,500,000",
			"Covered by authorised requisitions KES 55,500,000 (81%)",
		]);
		const items = wrapper.get('[data-testid="kt-anl-charts-items"]');
		expect(text(items)).toContain("Coverage by Plan item Covered Not yet covered");
		expect(text(items)).toContain("Servers Covered KES 25,000,000");
		expect(text(items)).toContain("Network switches Covered KES 8,000,000 Not yet covered KES 1,000,000");
		const split = wrapper.get('[data-testid="kt-anl-charts-split"]');
		expect(text(split)).toContain("Digital Health Covered KES 34,000,000 Not yet covered KES 12,000,000 74%");
		expect(text(split)).toContain("Human Resources Management and Development Covered KES 21,500,000 Not yet covered KES 1,000,000 96%");
		expect(text(split)).toContain("IT peripherals is shared: KES 4,000,000 is attributed to Digital Health and KES 2,500,000 to Human Resources Management and Development.");
		expect(wrapper.findAll(".kt-anl-fromzero-value").map((v) => v.text())).toEqual([
			"25 days after approved date", "7 days after approved date", "7 days after approved date", "On the approved date", "3 days before approved date", "No date recorded",
		]);
		expect(text(split)).toContain("Actual invitation date compared with the date approved in the Active Plan.");
		expect(wrapper.get('[data-testid="kt-anl-table"]').findAll("th").map((t) => t.text())).toEqual(["Plan item", "Department", "Planned value", "Covered by authorised requisitions", "Action"]);
		expect(wrapper.findAll('[data-testid="kt-anl-row"]')).toHaveLength(7);
		expect(text(wrapper.findAll('[data-testid="kt-anl-row"]')[0])).toBe("Clinic equipment Digital Health KES 12,000,000 KES 0 View record");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 7 of 7 Plan items");
		expect(wrapper.find('[data-testid="kt-anl-state"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="kt-anl-search"]').attributes("placeholder")).toBe("Search Plan item");
	});

	it("26: Needs shows compact rows and no table, with the monthly chart for Nov 2026", async () => {
		const wrapper = await open("26", boardUrl(FX["26"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("2 Needs accepted for planning No outstanding matters recorded in this selection.");
		expect(wrapper.find('[data-testid="kt-anl-table"]').exists()).toBe(false);
		expect(wrapper.findAll('[data-testid="kt-anl-row"]').map((r) => text(r))).toEqual([
			"Clinic equipment Accepted for planning View record",
			"Office furniture Accepted for planning View record",
		]);
		expect(text(wrapper.get('[data-testid="kt-anl-charts"]'))).toContain("Accepted for planning each month");
		expect(wrapper.findAll(".kt-anl-vbars-bar").map((b) => b.get("b").text())).toEqual(["2"]);
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 2 of 2 Needs");
		expect(wrapper.get('[data-testid="kt-anl-search"]').attributes("placeholder")).toBe("Search Need");
		expect(wrapper.get('[data-testid="kt-anl-state"]').findAll("option").map((o) => o.text())).toEqual(["All states", "Accepted for planning"]);
	});

	it("27: Departmental planning shows two plans accepted and its compact rows", async () => {
		const wrapper = await open("27", boardUrl(FX["27"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("2 departmental plans accepted No outstanding matters recorded in this selection.");
		expect(wrapper.findAll('[data-testid="kt-anl-row"]').map((r) => text(r))).toEqual([
			"Digital Health departmental plan Accepted View record",
			"Human Resources Management and Development departmental plan Accepted View record",
		]);
		expect(text(wrapper.get('[data-testid="kt-anl-charts"]'))).toContain("Departmental plans accepted each month");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 2 of 2 departmental plans");
	});

	it("30B: Peter's Annual planning shows the HRMD share note and four Plan items", async () => {
		const wrapper = await open("30B", boardUrl(FX["30B"]));
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toContain("4 Plan items in the Active Plan");
		expect(text(wrapper.get('[data-testid="kt-anl-charts-items"]'))).toContain("IT peripherals Human Resources Management and Development share Covered KES 2,500,000");
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 4 of 4 Plan items");
	});
});

// =============================================================================================================
describe("Overview variants: funding, departments, unavailable regions", () => {
	it("28: FY 2027/28 shows the Funding position after Time between key steps, the zero segment kept in the legend", async () => {
		const wrapper = await open("28", boardUrl(FX["28"]));
		expect(wrapper.get('[data-testid="kt-anl-fy"]').element.value).toBe("FY-2027-28");
		const region = wrapper.get('[data-testid="kt-anl-funding"]');
		expect(text(region)).toBe(
			"Funding position Ministry of Health procurement budget FY 2027/28 Current version 1 Registered allocation KES 150,000,000 " +
				"Reserved for requisitions KES 55,500,000 Committed to contracts KES 0 Available to reserve KES 94,500,000 " +
				"Available to reserve is not a cash balance. Committed to contracts is Budget's record of contract commitments; none is recorded.",
		);
		expect(region.findAll(".kt-anl-seg > span")).toHaveLength(2); // the zero segment has no width
		expect(wrapper.find('[data-testid="kt-anl-funding-message"]').exists()).toBe(false);
		const order = [...wrapper.element.querySelectorAll('[data-testid="kt-anl-steps"], [data-testid="kt-anl-funding"]')].map((n) => n.dataset.testid);
		expect(order).toEqual(["kt-anl-steps", "kt-anl-funding"]);
	});

	it("29F: the department funding view shows its own lines with a bar and the shared lines as two figures with no bar", async () => {
		const wrapper = await open("29F", boardUrl(FX["29F"]));
		const region = wrapper.get('[data-testid="kt-anl-funding"]');
		expect(text(region)).toBe(
			"Funding position Ministry of Health procurement budget FY 2027/28 Current version 1 Human Resources Management and Development " +
				"Budget lines available to Human Resources Management and Development Registered allocation KES 30,000,000 " +
				"Reserved for requisitions KES 13,500,000 Committed to contracts KES 0 Available to reserve KES 16,500,000 " +
				"Budget lines available to all departments Reserved for this department's requisitions KES 8,000,000 Committed to contracts for this department KES 0 " +
				"Budget lines available to all departments are shared, so their allocation and available amount are not divided by department. Available to reserve is not a cash balance.",
		);
		expect(region.findAll(".kt-anl-chart")).toHaveLength(1);
	});

	it("29: Peter's Overview shows the department scope and 96% coverage", async () => {
		const wrapper = await open("29", boardUrl(FX["29"]));
		expect(wrapper.get('[data-testid="kt-anl-scope"]').text()).toBe("Human Resources Management and Development");
		expect(text(wrapper.get('[data-testid="kt-anl-coverage"]'))).toContain("96% of planned value is covered by authorised requisitions");
		expect(text(wrapper.get('[data-testid="kt-anl-strip-tender_proceedings"]'))).toContain("4 Tenders Preparation 1 Open 1 Evaluation 1 Award 1 3 outstanding matters");
	});

	it("31C: the unavailable Needs column shows its sentence and Try again; the other four are unchanged", async () => {
		const wrapper = await open("31C", boardUrl(FX["31C"]));
		const needs = wrapper.get('[data-testid="kt-anl-strip-needs"]');
		expect(text(needs)).toBe("Needs Needs could not be loaded. Try again");
		expect(needs.find(".kt-anl-chart").exists()).toBe(false);
		expect(wrapper.get('[data-testid="kt-anl-strip-tender_proceedings"]').text()).toContain("4 outstanding matters");
		expect(wrapper.get('[data-testid="kt-anl-waiting"]').exists()).toBe(true);
		expect(wrapper.get('[data-testid="kt-anl-steps"]').exists()).toBe(true);
		await wrapper.get('[data-testid="kt-anl-definitions-toggle"]').trigger("click");
		expect(wrapper.get('[data-testid="kt-anl-definitions-body"]').text().endsWith("The Needs read is unavailable. Other area reads completed at 10:00 EAT.")).toBe(true);
	});

	it("31E: unavailable coverage shows its sentence and Try again, and the Annual planning column says Coverage unavailable", async () => {
		const wrapper = await open("31E", boardUrl(FX["31E"]));
		expect(text(wrapper.get('[data-testid="kt-anl-coverage"]'))).toBe("Plan coverage Plan coverage could not be loaded. Try again");
		expect(wrapper.get('[data-testid="kt-anl-coverage"]').find(".kt-result-value").exists()).toBe(false);
		const annual = wrapper.get('[data-testid="kt-anl-strip-annual_planning"]');
		expect(text(annual)).toBe("Annual planning 7 Plan items in the Active Plan Coverage unavailable No outstanding matters recorded View annual planning");
		expect(annual.find(".kt-anl-chart").exists()).toBe(false);
	});

	it("31J: the Technical Operator sees exactly the Overview", async () => {
		const wrapper = await open("31J", boardUrl(FX["31J"]));
		expect(text(wrapper.get('[data-testid="kt-anl-strip-needs"]'))).toContain("2 Needs");
		expect(wrapper.findAll("button").map((b) => b.text())).toEqual(["Refresh", "Apply filters", "How these figures are counted"]);
	});
});

// =============================================================================================================
describe("state panels", () => {
	it("31B: no records in the selection: one line and Clear filters, no strip or charts, a plain icon", async () => {
		const wrapper = await open("31B", boardUrl(FX["31B"]));
		expect(text(wrapper.get('[data-testid="kt-anl-empty"]'))).toBe("No records are available in this selection. Clear filters");
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(false);
		expect(wrapper.find(".kt-anl-chart").exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-definitions"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-empty"] .kt-icon.is-lg').exists()).toBe(true);
		expect(wrapper.findAll(".kt-tab")).toHaveLength(6);
	});

	it("31B: Clear filters in the panel pushes the tab route without filters", async () => {
		setUrl("/desk/analytics?fy=FY-2027-28");
		const wrapper = await open("31B");
		await wrapper.get('[data-testid="kt-anl-empty-clear"]').trigger("click");
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics");
	});

	it("31D: all reads failed: header, tabs and filters, the line and a primary Try again; no update time, strip or definitions", async () => {
		const wrapper = await open("31D", boardUrl(FX["31D"]));
		expect(text(wrapper.get('[data-testid="kt-anl-failed"]'))).toBe("Analytics could not be loaded. Try again");
		expect(wrapper.get('[data-testid="kt-anl-retry-all"]').classes()).toContain("btn-primary");
		expect(wrapper.find('[data-testid="kt-anl-updated"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-definitions"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-failed"] .kt-spot.is-error').exists()).toBe(true);
		expect(wrapper.findAll(".kt-tab")).toHaveLength(6);
		analyticsApi.load.mockResolvedValue(clone(FX["21"]));
		await wrapper.get('[data-testid="kt-anl-retry-all"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(true);
	});

	it("31D: a call that throws draws the same failed state, never a zero", async () => {
		analyticsApi.load.mockRejectedValue(new Error("boom"));
		const wrapper = mountPage();
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-anl-failed"]'))).toBe("Analytics could not be loaded. Try again");
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(false);
	});

	it("31G: first paint with no data shows Loading Analytics…, the title, the description and the tabs, and no counts", async () => {
		analyticsApi.load.mockReturnValue(new Promise(() => {}));
		const wrapper = mountPage();
		await flushPromises();
		expect(wrapper.get('[data-testid="kt-anl-loading"]').text()).toBe("Loading Analytics…");
		expect(wrapper.get('[data-testid="kt-anl-title"]').text()).toBe("Procurement Analytics");
		expect(wrapper.findAll(".kt-tab").map((t) => t.text())).toEqual(["Overview", "Needs", "Departmental planning", "Annual planning", "Requisitions", "Tender proceedings"]);
		expect(wrapper.find('[data-testid="kt-anl-filters"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-updated"]').exists()).toBe(false);
		expect(text(wrapper)).not.toMatch(/outstanding|KES|Tenders|Requisitions \d/);
		expect(wrapper.get("main").attributes("aria-busy")).toBe("true");
	});

	it("31H: no permitted area: the shared access state, no tabs, filters, totals or actions", async () => {
		const wrapper = await open("31H", boardUrl(FX["31H"]));
		expect(wrapper.get('[data-testid="kt-anl-denied"] h2').text()).toBe("You do not have access to Analytics");
		expect(wrapper.get('[data-testid="kt-anl-denied"] p').text()).toBe("No Analytics records are available to your responsibilities.");
		expect(wrapper.find(".kt-tabs").exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-filters"]').exists()).toBe(false);
		expect(wrapper.find("button").exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-denied"] .kt-spot.is-neutral').exists()).toBe(true);
	});

	it("draws the spot illustration only on 31B, 31D and 31H", async () => {
		for (const id of Object.keys(FX)) {
			document.body.innerHTML = "";
			const wrapper = await open(id, boardUrl(FX[id]));
			const has = wrapper.find(".kt-spot").exists() || !!wrapper.find('[data-testid="kt-anl-empty"] .kt-icon').exists();
			expect([id, has]).toEqual([id, ["31B", "31D", "31H"].includes(id)]);
			wrapper.unmount();
			mounted.pop();
		}
	});

	it("a denied verdict reads like 31H", async () => {
		const payload = clone(FX["31H"]);
		payload.verdict = "denied";
		const wrapper = await open("31H", undefined, payload);
		expect(wrapper.get('[data-testid="kt-anl-denied"] p').text()).toBe("No Analytics records are available to your responsibilities.");
	});
});

// =============================================================================================================
describe("URL state (route_spike.md, ANL §9.1)", () => {
	it("reads the tab from the path and fy, dept and state from location.search for its first read, never from route_options", async () => {
		await open("23", "/desk/analytics/tender-proceedings?fy=FY-2027-28&dept=OU-DH&state=award");
		expect(analyticsApi.load).toHaveBeenCalledTimes(1);
		expect(lastCall()).toEqual({ tab: "tender-proceedings", fy: "FY-2027-28", dept: "OU-DH", state: "award", search: "", cursor: null });
	});

	it("a tab click pushes the tab route keeping fy and dept, dropping state", async () => {
		const wrapper = await open("23", "/desk/analytics/tender-proceedings?fy=FY-2027-28&dept=OU-DH&state=award");
		const push = vi.spyOn(window.history, "pushState");
		await wrapper.get('.kt-tab input[value="requisitions"]').setValue();
		await flushPromises();
		expect(push).toHaveBeenCalledTimes(1);
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/requisitions?fy=FY-2027-28&dept=OU-DH");
		expect(frappe.router.route).toHaveBeenCalled();
		expect(lastCall()).toMatchObject({ tab: "requisitions", fy: "FY-2027-28", dept: "OU-DH", state: "" });
		expect(wrapper.get('.kt-tab input:checked').element.value).toBe("requisitions");
		await wrapper.get('.kt-tab input[value="overview"]').setValue();
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics?fy=FY-2027-28&dept=OU-DH");
	});

	it("takes the prefix from the current address, never hard-coded", async () => {
		const wrapper = await open("21", "/app/analytics");
		await wrapper.get('.kt-tab input[value="needs"]').setValue();
		expect(window.location.pathname).toBe("/app/analytics/needs");
	});

	it("Apply filters pushes fy and dept; choosing in a select pushes nothing until then", async () => {
		const wrapper = await open("21", "/desk/analytics/needs");
		const push = vi.spyOn(window.history, "pushState");
		await wrapper.get('[data-testid="kt-anl-fy"]').setValue("FY-2027-28");
		await wrapper.get('[data-testid="kt-anl-dept"]').setValue("OU-HR");
		expect(push).not.toHaveBeenCalled();
		expect(window.location.search).toBe("");
		await wrapper.get('[data-testid="kt-anl-apply"]').trigger("click");
		await flushPromises();
		expect(push).toHaveBeenCalledTimes(1);
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/needs?fy=FY-2027-28&dept=OU-HR");
		expect(lastCall()).toMatchObject({ tab: "needs", fy: "FY-2027-28", dept: "OU-HR" });
	});

	it("the selects follow the caller's own pending selection, not the server's echo", async () => {
		const wrapper = await open("21");
		await wrapper.get('[data-testid="kt-anl-fy"]').setValue("FY-2027-28");
		// a re-read lands whose echo says fy is "" (nothing applied yet): the select must not snap back
		await wrapper.get('[data-testid="kt-anl-refresh"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="kt-anl-fy"]').element.value).toBe("FY-2027-28");
		expect(window.location.search).toBe("");
	});

	it("Clear filters removes fy, dept and state, keeps the tab, and clears the search text", async () => {
		const wrapper = await open("23", "/desk/analytics/tender-proceedings?fy=FY-2027-28&dept=OU-DH&state=award");
		await wrapper.get('[data-testid="kt-anl-search"]').setValue("lab");
		const push = vi.spyOn(window.history, "pushState");
		await wrapper.get('[data-testid="kt-anl-clear-filters"]').trigger("click");
		await flushPromises();
		expect(push).toHaveBeenCalledTimes(1);
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/tender-proceedings");
		expect(lastCall()).toMatchObject({ tab: "tender-proceedings", fy: "", dept: "", state: "", search: "" });
		expect(wrapper.get('[data-testid="kt-anl-search"]').element.value).toBe("");
		expect(wrapper.get('[data-testid="kt-anl-fy"]').element.value).toBe("");
	});

	it("the state select applies at once by pushing state, keeping fy and dept", async () => {
		const wrapper = await open("22", "/desk/analytics/tender-proceedings?fy=FY-2027-28");
		await wrapper.get('[data-testid="kt-anl-state"]').setValue("open");
		await flushPromises();
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/tender-proceedings?fy=FY-2027-28&state=open");
		expect(lastCall()).toMatchObject({ state: "open", fy: "FY-2027-28" });
		await wrapper.get('[data-testid="kt-anl-state"]').setValue("");
		expect(window.location.search).toBe("?fy=FY-2027-28");
	});

	it("strip links and View annual planning push the named tab with the current fy and dept", async () => {
		const wrapper = await open("21", "/desk/analytics?fy=FY-2027-28&dept=OU-DH");
		await wrapper.get('[data-testid="kt-anl-strip-needs"] a').trigger("click");
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/needs?fy=FY-2027-28&dept=OU-DH");
		wrapper.unmount();
		mounted.pop();
		document.body.innerHTML = "";
		const again = await open("21", "/desk/analytics?fy=FY-2027-28&dept=OU-DH");
		expect(again.get('[data-testid="kt-anl-strip-needs"] a').attributes("href")).toBe("/desk/analytics/needs?fy=FY-2027-28&dept=OU-DH");
		await again.get('[data-testid="kt-anl-coverage"] a').trigger("click");
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/annual-planning?fy=FY-2027-28&dept=OU-DH");
	});

	it("Back and Forward re-read location.search (never route_options) and re-read the server", async () => {
		const wrapper = await open("21", "/desk/analytics?fy=FY-2027-28");
		await wrapper.get('[data-testid="kt-anl-fy"]').setValue("");
		await wrapper.get('[data-testid="kt-anl-dept"]').setValue("OU-HR");
		await wrapper.get('[data-testid="kt-anl-apply"]').trigger("click");
		await flushPromises();
		expect(window.location.search).toBe("?dept=OU-HR");
		expect(lastCall()).toMatchObject({ fy: "", dept: "OU-HR" });
		window.history.back();
		await tick();
		await flushPromises();
		expect(window.location.search).toBe("?fy=FY-2027-28");
		expect(lastCall()).toMatchObject({ tab: "overview", fy: "FY-2027-28", dept: "", state: "" });
		expect(wrapper.get('[data-testid="kt-anl-fy"]').element.value).toBe("FY-2027-28");
		expect(wrapper.get('[data-testid="kt-anl-dept"]').element.value).toBe("");
		window.history.forward();
		await tick();
		await flushPromises();
		expect(window.location.search).toBe("?dept=OU-HR");
		expect(lastCall()).toMatchObject({ fy: "", dept: "OU-HR" });
		expect(frappe.route_options.fy).toBe("STALE-FROM-ROUTE-OPTIONS"); // untouched and never read
		for (const call of analyticsApi.load.mock.calls) expect(call[0].fy).not.toBe("STALE-FROM-ROUTE-OPTIONS");
	});

	it("Back to another tab re-reads that tab", async () => {
		const wrapper = await open("21", "/desk/analytics");
		await wrapper.get('.kt-tab input[value="needs"]').setValue();
		await flushPromises();
		expect(lastCall().tab).toBe("needs");
		window.history.back();
		await tick();
		await flushPromises();
		expect(window.location.pathname).toBe("/desk/analytics");
		expect(lastCall().tab).toBe("overview");
		expect(wrapper.get('.kt-tab input:checked').element.value).toBe("overview");
	});

	it("a Back to a different page is not read as this page's route", async () => {
		await open("21", "/desk/analytics?fy=A");
		const calls = analyticsApi.load.mock.calls.length;
		window.history.pushState(null, "", "/desk/home");
		window.dispatchEvent(new PopStateEvent("popstate"));
		await flushPromises();
		expect(analyticsApi.load.mock.calls.length).toBe(calls);
	});

	it("search text is component state: Enter reads with it, and neither the URL nor the history changes", async () => {
		const wrapper = await open("22", "/desk/analytics/tender-proceedings?state=award");
		const push = vi.spyOn(window.history, "pushState");
		const replace = vi.spyOn(window.history, "replaceState");
		await wrapper.get('[data-testid="kt-anl-search"]').setValue("laboratory");
		expect(analyticsApi.load).toHaveBeenCalledTimes(1); // typing alone reads nothing
		await wrapper.get('[data-testid="kt-anl-search"]').trigger("keydown", { key: "Enter" });
		await flushPromises();
		expect(analyticsApi.load).toHaveBeenCalledTimes(2);
		expect(lastCall()).toMatchObject({ search: "laboratory", state: "award", tab: "tender-proceedings", cursor: null });
		expect(window.location.search).toBe("?state=award");
		expect(push).not.toHaveBeenCalled();
		expect(replace).not.toHaveBeenCalled();
		expect(frappe.router.route).not.toHaveBeenCalled();
	});

	it("Clear search removes only the search, keeping year, department and state", async () => {
		const payload = clone(FX["31A"]);
		const wrapper = await open("31A", "/desk/analytics/tender-proceedings?fy=FY-2027-28&state=award", payload);
		await wrapper.get('[data-testid="kt-anl-search"]').setValue("laboratory");
		await wrapper.get('[data-testid="kt-anl-search"]').trigger("keydown", { key: "Enter" });
		await flushPromises();
		analyticsApi.load.mockResolvedValue(clone(FX["23"]));
		await wrapper.get('[data-testid="kt-anl-clear-register"]').trigger("click");
		await flushPromises();
		expect(lastCall()).toMatchObject({ search: "", fy: "FY-2027-28", state: "award", tab: "tender-proceedings" });
		expect(wrapper.get('[data-testid="kt-anl-search"]').element.value).toBe("");
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics/tender-proceedings?fy=FY-2027-28&state=award");
	});

	it("a new tab starts with no search text", async () => {
		const wrapper = await open("22", "/desk/analytics/tender-proceedings");
		await wrapper.get('[data-testid="kt-anl-search"]').setValue("lab");
		await wrapper.get('[data-testid="kt-anl-search"]').trigger("keydown", { key: "Enter" });
		await flushPromises();
		analyticsApi.load.mockResolvedValue(clone(FX["24"]));
		await wrapper.get('.kt-tab input[value="requisitions"]').setValue();
		await flushPromises();
		expect(lastCall()).toMatchObject({ tab: "requisitions", search: "" });
		expect(wrapper.get('[data-testid="kt-anl-search"]').element.value).toBe("");
	});

	// The server's answer for an invalid or unpermitted value (ANL §8, AC-13): the messages, the valid parts of the
	// selection, the option lists, `invalid: true` and no regions. The goldens hold no such case, so it is built here.
	function invalidPayload(base, over = {}) {
		const payload = clone(FX[base]);
		payload.overview = null;
		payload.area = null;
		payload.empty = false;
		payload.definitions = "";
		payload.filters = { ...payload.filters, invalid: true, messages: ["Choose an available financial year."], ...over };
		return payload;
	}

	it("an invalid filter shows the message(s), keeps the valid part, and draws no region, strip, register or definitions", async () => {
		const payload = invalidPayload("21", { dept: "OU-DH", fy: "" });
		const wrapper = await open("21", "/desk/analytics?fy=FY-BOGUS&dept=OU-DH", payload);
		expect(lastCall()).toMatchObject({ fy: "FY-BOGUS", dept: "OU-DH" });
		expect(wrapper.get('[data-testid="kt-anl-filter-messages"]').text()).toBe("Choose an available financial year.");
		expect(wrapper.get('[data-testid="kt-anl-dept"]').element.value).toBe("OU-DH");
		// no option is chosen for a value the server refused: nothing is silently widened to "All years"
		expect(wrapper.get('[data-testid="kt-anl-fy"]').element.selectedIndex).toBe(-1);
		expect(window.location.search).toBe("?fy=FY-BOGUS&dept=OU-DH");
		// the header, the tabs, the filter row and Clear filters stay; nothing else does
		expect(wrapper.find('[data-testid="kt-anl-header"]').exists()).toBe(true);
		expect(wrapper.findAll(".kt-tab")).toHaveLength(6);
		expect(wrapper.get('[data-testid="kt-anl-clear-filters"]').text()).toBe("Clear filters");
		for (const id of ["strip", "waiting", "coverage", "steps", "funding", "funding-message", "register", "definitions", "area-result", "charts", "outstanding", "empty", "failed"]) {
			expect([id, wrapper.find(`[data-testid="kt-anl-${id}"]`).exists()]).toEqual([id, false]);
		}
		expect(wrapper.find(".kt-anl-chart").exists()).toBe(false);
		expect(wrapper.find(".kt-kpi-card").exists()).toBe(false);
	});

	it("an invalid filter on an area tab draws the same: messages only, the valid state kept, no register", async () => {
		const payload = invalidPayload("22", { fy: "", state: "", messages: ["Choose an available financial year.", "Choose an available state."] });
		const wrapper = await open("22", "/desk/analytics/tender-proceedings?fy=bogus&state=nonsense", payload);
		expect(lastCall()).toMatchObject({ tab: "tender-proceedings", fy: "bogus", state: "nonsense" });
		expect(wrapper.findAll('[data-testid="kt-anl-filter-messages"] li').map((li) => li.text())).toEqual(["Choose an available financial year.", "Choose an available state."]);
		expect(wrapper.find('[data-testid="kt-anl-register"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-table"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-definitions"]').exists()).toBe(false);
		expect(wrapper.get('.kt-tab input:checked').element.value).toBe("tender-proceedings");
	});

	it("Clear filters from an invalid view pushes the tab route without filters and the regions come back", async () => {
		const wrapper = await open("21", "/desk/analytics?fy=bogus", invalidPayload("21"));
		analyticsApi.load.mockResolvedValue(clone(FX["21"]));
		await wrapper.get('[data-testid="kt-anl-clear-filters"]').trigger("click");
		await flushPromises();
		expect(window.location.pathname + window.location.search).toBe("/desk/analytics");
		expect(lastCall()).toMatchObject({ fy: "", dept: "", state: "" });
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-anl-filter-messages"]').exists()).toBe(false);
	});

	it("an unknown tab segment is read as Overview", async () => {
		await open("21", "/desk/analytics/nonsense");
		expect(lastCall().tab).toBe("overview");
	});
});

// =============================================================================================================
describe("re-reads, retries and paging", () => {
	it("Try again re-reads and replaces only the failed region; the others keep their elements", async () => {
		const wrapper = await open("31C", boardUrl(FX["31C"]));
		const requisitions = wrapper.get('[data-testid="kt-anl-strip-requisitions"]').element;
		const coverage = wrapper.get('[data-testid="kt-anl-coverage"]').element;
		const waiting = wrapper.get('[data-testid="kt-anl-waiting"]').element;
		analyticsApi.load.mockResolvedValue(clone(FX["21"]));
		await wrapper.get('[data-testid="kt-anl-strip-needs"] [data-testid="kt-anl-retry"]').trigger("click");
		await flushPromises();
		expect(analyticsApi.load).toHaveBeenCalledTimes(2);
		expect(text(wrapper.get('[data-testid="kt-anl-strip-needs"]'))).toBe("Needs 2 Needs Accepted for planning 2 No outstanding matters recorded View Needs");
		expect(wrapper.get('[data-testid="kt-anl-strip-requisitions"]').element).toBe(requisitions);
		expect(wrapper.get('[data-testid="kt-anl-coverage"]').element).toBe(coverage);
		expect(wrapper.get('[data-testid="kt-anl-waiting"]').element).toBe(waiting);
		expect(wrapper.find('[data-testid="kt-anl-loading"]').exists()).toBe(false);
	});

	it("Try again on Plan coverage fills the region and the Annual planning column's bar", async () => {
		const wrapper = await open("31E", boardUrl(FX["31E"]));
		analyticsApi.load.mockResolvedValue(clone(FX["21"]));
		await wrapper.get('[data-testid="kt-anl-coverage"] [data-testid="kt-anl-retry"]').trigger("click");
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-anl-coverage"]'))).toContain("81% of planned value is covered by authorised requisitions");
		expect(text(wrapper.get('[data-testid="kt-anl-strip-annual_planning"]'))).toContain("Fully covered 5");
	});

	it("a Try again that still fails says so and leaves the region as it was", async () => {
		const wrapper = await open("31C", boardUrl(FX["31C"]));
		analyticsApi.load.mockRejectedValue(new Error("boom"));
		await wrapper.get('[data-testid="kt-anl-strip-needs"] [data-testid="kt-anl-retry"]').trigger("click");
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-anl-strip-needs"]'))).toContain("Needs could not be loaded.");
		expect(text(wrapper.get('[data-testid="kt-anl-strip-needs"]'))).toContain("Still could not be loaded.");
		expect(wrapper.get('[data-testid="kt-anl-strip-requisitions"]').text()).toContain("7");
	});

	it("a second render re-reads in place: no loading line, the old figures stay and data-refreshing shows meanwhile", async () => {
		const wrapper = await open("21");
		let resolve;
		analyticsApi.load.mockReturnValue(new Promise((r) => (resolve = r)));
		await wrapper.get('[data-testid="kt-anl-refresh"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-anl-loading"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="kt-anl-strip-needs"]').text()).toContain("2");
		expect(wrapper.get("main").attributes("data-refreshing")).toBe("true");
		resolve(clone(FX["21"]));
		await flushPromises();
		expect(wrapper.get("main").attributes("data-refreshing")).toBeUndefined();
		expect(analyticsApi.load).toHaveBeenCalledTimes(2);
	});

	it("showing the page again on the same route revalidates in place (epoch)", async () => {
		const wrapper = await open("21");
		epochRef.value += 1;
		await flushPromises();
		expect(analyticsApi.load).toHaveBeenCalledTimes(2);
		expect(wrapper.find('[data-testid="kt-anl-loading"]').exists()).toBe(false);
	});

	it("a screen already loaded in this session renders from the cache at once when its tab is opened again", async () => {
		const wrapper = await open("21");
		analyticsApi.load.mockResolvedValue(clone(FX["22"]));
		await wrapper.get('.kt-tab input[value="tender-proceedings"]').setValue();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-anl-register"]').exists()).toBe(true);
		let resolve;
		analyticsApi.load.mockReturnValue(new Promise((r) => (resolve = r)));
		await wrapper.get('.kt-tab input[value="overview"]').setValue();
		expect(wrapper.find('[data-testid="kt-anl-loading"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(true);
		resolve(clone(FX["21"]));
		await flushPromises();
	});

	it("an older slower read never overwrites a newer one", async () => {
		const wrapper = await open("21");
		let slow;
		analyticsApi.load.mockReturnValueOnce(new Promise((r) => (slow = r)));
		await wrapper.get('[data-testid="kt-anl-refresh"]').trigger("click");
		analyticsApi.load.mockResolvedValue(clone(FX["22"]));
		await wrapper.get('.kt-tab input[value="tender-proceedings"]').setValue();
		await flushPromises();
		slow(clone(FX["21"]));
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-anl-register"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-anl-strip"]').exists()).toBe(false);
	});

	it("Next reads the server's cursor, Previous goes back, and neither enters the URL", async () => {
		const first = clone(FX["22"]);
		first.area.register.next_cursor = "CURSOR-1";
		first.area.register.footer = "Showing 1 of 6 Tenders";
		const second = clone(FX["22"]);
		second.area.register.next_cursor = null;
		second.area.register.footer = "Showing 6 of 6 Tenders";
		const wrapper = await open("22", "/desk/analytics/tender-proceedings", first);
		expect(wrapper.get('[data-testid="kt-anl-previous"]').attributes("disabled")).toBeDefined();
		analyticsApi.load.mockResolvedValue(second);
		await wrapper.get('[data-testid="kt-anl-next"]').trigger("click");
		await flushPromises();
		expect(lastCall()).toMatchObject({ cursor: "CURSOR-1" });
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 6 of 6 Tenders");
		expect(wrapper.get('[data-testid="kt-anl-next"]').attributes("disabled")).toBeDefined();
		expect(window.location.search).toBe("");
		analyticsApi.load.mockResolvedValue(first);
		await wrapper.get('[data-testid="kt-anl-previous"]').trigger("click");
		await flushPromises();
		expect(lastCall().cursor).toBeNull();
		expect(wrapper.get('[data-testid="kt-anl-footer"]').text()).toBe("Showing 1 of 6 Tenders");
	});

	it("a Partial list is labelled as such, and a partial area shows no display figure", async () => {
		const payload = clone(FX["22"]);
		payload.area.partial = true;
		payload.area.result_text = "Tender proceedings totals are unavailable.";
		payload.area.register.partial = true;
		const wrapper = await open("22", "/desk/analytics/tender-proceedings", payload);
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("Tender proceedings totals are unavailable.");
		expect(wrapper.find('[data-testid="kt-anl-area-result"] .kt-result-value').exists()).toBe(false);
		expect(wrapper.get('[data-testid="kt-anl-partial"]').text()).toBe("Partial list");
	});

	it("an unavailable area tab shows the sentence and Try again, and no zero", async () => {
		const payload = clone(FX["22"]);
		payload.area = { key: "tender_proceedings", tab: "tender-proceedings", label: "Tender proceedings", icon: "tender-proceedings", status: "unavailable", message: "Tender proceedings could not be loaded.", retry: true };
		const wrapper = await open("22", "/desk/analytics/tender-proceedings", payload);
		expect(wrapper.get('[data-testid="kt-anl-region-error"]').text()).toContain("Tender proceedings could not be loaded.");
		expect(wrapper.find('[data-testid="kt-anl-register"]').exists()).toBe(false);
		analyticsApi.load.mockResolvedValue(clone(FX["22"]));
		await wrapper.get('[data-testid="kt-anl-retry"]').trigger("click");
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-anl-area-result"]'))).toBe("6 Tenders");
	});

	it("View record opens the owner's route through frappe.set_route", async () => {
		const wrapper = await open("22", boardUrl(FX["22"]));
		const link = wrapper.findAll('[data-testid="kt-anl-row"]')[0].get("a");
		expect(link.attributes("href")).toBe("/desk/technical-search/T-041");
		await link.trigger("click");
		expect(frappe.set_route).toHaveBeenCalledWith("technical-search", "T-041");
		expect(window.location.pathname).toBe("/desk/analytics/tender-proceedings");
	});

	it("a row with no permitted route has no action", async () => {
		const payload = clone(FX["22"]);
		payload.area.register.rows[0].action.route = null;
		const wrapper = await open("22", "/desk/analytics/tender-proceedings", payload);
		expect(wrapper.findAll('[data-testid="kt-anl-row"]')[0].find("a").exists()).toBe(false);
	});
});

// =============================================================================================================
describe("keyboard and accessibility", () => {
	it("every control is reachable by keyboard: tabs, selects, search, buttons, links and the disclosure", async () => {
		const wrapper = await open("23", boardUrl(FX["23"]));
		const controls = [...wrapper.element.querySelectorAll("button, a[href], select, input")].filter((el) => !el.disabled);
		expect(controls.length).toBeGreaterThan(15);
		for (const control of controls) {
			expect(control.getAttribute("tabindex")).not.toBe("-1");
			control.focus();
			expect(document.activeElement).toBe(control);
		}
		const kinds = new Set(controls.map((c) => c.tagName + (c.type ? ":" + c.type : "")));
		expect(kinds).toEqual(new Set(["INPUT:radio", "SELECT:select-one", "INPUT:search", "BUTTON:button", "A"]));
		expect(wrapper.findAll(".kt-tab input")).toHaveLength(6);
		expect(wrapper.get('[data-testid="kt-anl-fy"]').attributes("id")).toBe("kt-anl-fy");
		expect(wrapper.get('label[for="kt-anl-fy"]').text()).toBe("Financial year");
		expect(wrapper.get('label[for="kt-anl-search"]').text()).toBe("Search");
	});

	it("the disclosure button toggles with the keyboard's click and names the region it controls", async () => {
		const wrapper = await open("21");
		const toggle = wrapper.get('[data-testid="kt-anl-definitions-toggle"]');
		expect(toggle.element.tagName).toBe("BUTTON");
		expect(toggle.attributes("aria-controls")).toBe("kt-anl-definitions-body");
		toggle.element.focus();
		toggle.element.click();
		await flushPromises();
		expect(toggle.attributes("aria-expanded")).toBe("true");
		expect(document.getElementById("kt-anl-definitions-body")).not.toBeNull();
	});

	it("every chart exposes its values as a table for assistive technology, in the visual order, with no visible toggle", async () => {
		const wrapper = await open("22", boardUrl(FX["22"]));
		const tables = wrapper.findAll("table.sr-only");
		expect(tables.length).toBeGreaterThanOrEqual(3);
		const stages = tables.find((t) => t.text().includes("Tenders by stage"));
		expect(stages.findAll("tbody tr").map((r) => r.findAll("th,td").map((c) => c.text())[0])).toEqual([
			"Tender preparation and publication", "Open for bids", "Evaluation", "Award", "Closed",
		]);
	});
});

// =============================================================================================================
describe("the page draws the presentation fields the server sends, with no rule of its own", () => {
	it("the register heading is register.title", async () => {
		const payload = clone(FX["22"]);
		payload.area.register.title = "Tendering records";
		const wrapper = await open("22", "/desk/analytics/tender-proceedings", payload);
		expect(wrapper.get('[data-testid="kt-anl-register"] h2').text()).toBe("Tendering records");
		for (const [id, title] of [["22", "Tenders"], ["24", "Requisitions"], ["25", "Plan items"], ["26", "Needs"], ["27", "Departmental plans"]]) {
			document.body.innerHTML = "";
			const w = await open(id, boardUrl(FX[id]));
			expect([id, w.get('[data-testid="kt-anl-register"] h2').text()]).toEqual([id, title]);
			w.unmount();
			mounted.pop();
		}
	});

	it("an outstanding line carries the hourglass only when has_matters says so, whatever the sentence starts with", async () => {
		const wrapper = await open("21");
		const icons = wrapper.findAll(".kt-ap-out").map((o) => o.find(".kt-icon").exists());
		expect(icons).toEqual([false, false, false, true, true]);
		const payload = clone(FX["21"]);
		payload.overview.strip.columns[0].outstanding = "3 things";
		payload.overview.strip.columns[0].has_matters = false;
		payload.overview.strip.columns[1].outstanding = "Nothing";
		payload.overview.strip.columns[1].has_matters = true;
		document.body.innerHTML = "";
		const again = await open("21", undefined, payload);
		expect(again.findAll(".kt-ap-out").map((o) => o.classes().includes("has-matters"))).toEqual([false, true, false, true, true]);
	});

	it("the month axis is the server's axis_lines", async () => {
		const payload = clone(FX["22"]);
		payload.area.charts.monthly.months[2].axis_lines = ["Sep", "marker"];
		const wrapper = await open("22", "/desk/analytics/tender-proceedings", payload);
		expect(text(wrapper.get(".kt-anl-vbars-axis"))).toContain("Sep marker");
	});

	it("a cell is muted only when the server marks it quiet", async () => {
		const wrapper = await open("22", boardUrl(FX["22"]));
		const muted = wrapper.findAll('[data-testid="kt-anl-row"] .kt-ap-cell-muted').map((n) => n.text());
		const expected = FX["22"].area.register.rows.filter((r) => r.cells.recorded_ao_outcome.quiet).map((r) => r.cells.recorded_ao_outcome.text);
		expect(muted).toEqual(expected);
		expect(muted.length).toBeGreaterThan(0);
		const payload = clone(FX["22"]);
		payload.area.register.rows.forEach((r) => (r.cells.recorded_ao_outcome.quiet = false));
		document.body.innerHTML = "";
		const again = await open("22", "/desk/analytics/tender-proceedings", payload);
		expect(again.findAll(".kt-ap-cell-muted")).toHaveLength(0);
	});

	it("the Coverage by Plan item legend is the server's, Covered and Not yet covered both", async () => {
		const wrapper = await open("30B", boardUrl(FX["30B"]));
		const legend = wrapper.get('[data-testid="kt-anl-charts-items"] .kt-anl-legend');
		expect(legend.findAll("span").map((s) => s.text())).toEqual(["Covered", "Not yet covered"]);
	});

	it("the applied state is among the State options (server), so the select shows it", async () => {
		const payload = clone(FX["22"]);
		payload.filters.state = "award";
		const wrapper = await open("22", "/desk/analytics/tender-proceedings?state=award", payload);
		expect(wrapper.get('[data-testid="kt-anl-state"]').element.value).toBe("award");
	});

	it("31F: the Tender whose stage could not be read has an outstanding row with no waiting badge", async () => {
		const wrapper = await open("31F", boardUrl(FX["31F"]));
		const rows = wrapper.findAll('[data-testid="kt-anl-orow"]');
		expect(rows.map((r) => text(r))).toContain("Supply of printers We could not load the current position.");
		const row = rows.find((r) => text(r).startsWith("Supply of printers"));
		expect(row.find(".kt-ap-badge").exists()).toBe(false);
		expect(row.find(".kt-ap-since").exists()).toBe(false);
	});
});
