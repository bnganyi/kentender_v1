// HOME-CHG-001 v0.6 — Home. The payloads are shaped as `get_home_workspace` returns them and carry the
// strings of design/Home/Home.dc.html (HOME-DES-21, 22, 23, 25, 26/26B, 27, 28A-28F); the page makes no
// phrase of its own, so every expected string below is one the server sends.
import { flushPromises, mount } from "@vue/test-utils";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./data/homeApi.js", () => ({ homeApi: { load: vi.fn() } }));

import Home from "./Home.vue";
import { layoutOf } from "./composables/useHomeWorkspace.js";
import { homeApi } from "./data/homeApi.js";

const dest = (route, route_options = {}) => ({ route, route_options });

function entry(over = {}) {
	return {
		key: "tenders|TND-1|a", owner: "tenders", module: "Tenders", title: "Supply of UPS units", reference: "", action: "Do the thing",
		reason: "", blocked: false, holder: "", fact: "", link: null, sentence: "", destination: dest(["tenders", "TND-1"]), primary: false,
		timing: "", due: "", badge: "", exact: "", ...over,
	};
}

function region(entries, over = {}) {
	return {
		applicable: true, coverage: "complete", count: entries.length, label: "", total: entries.length, next_count: 0,
		entries, shown: entries.length, remaining: 0, paged: false, next_cursor: null, ...over,
	};
}

const NA = () => region([], { applicable: false, coverage: "not_applicable", count: null, total: null });

function payload(over = {}) {
	return {
		state: "ready", empty: false, summary_visible: true, providers: { configured: 9, failed: 0 },
		viewer: { greeting: "Good morning", first_name: "Charles", technical: false, responsibilities: { items: [], line: "Head of Procurement Function, site-wide" } },
		updated: "18 June 2027, 10:00 EAT",
		regions: { my_work: NA(), coming_up: NA(), waiting: NA(), oversight: NA(), completed: NA() },
		...over,
	};
}

// HOME-DES-21: Charles (H10)
function charles() {
	return payload({
		regions: {
			my_work: region([
				entry({ key: "req", owner: "requisitions", module: "Requisitions", title: "Clinic equipment requisition", action: "Authorise requisition", timing: "Received 2 days ago (16 June, 11:00)", primary: true, destination: dest(["procurement-requisitions", "procurement-task", "T-1"]) }),
				entry({ key: "opinion", owner: "award", module: "Award", title: "Supply of printers", reference: "TND-MOH-2027-044", action: "Prepare professional opinion", timing: "Received 2 days ago (16 June, 14:07)", destination: dest(["award", "AWD-1"], { tab: "opinion" }) }),
				entry({ key: "notice", owner: "award", module: "Award", title: "Supply of monitors", reference: "TND-MOH-2027-045", action: "Resolve notice delivery", timing: "Received yesterday (17 June, 11:00)", reason: "A required notice is not yet confirmed.", blocked: false, destination: dest(["award", "AWD-2"]) }),
			], { label: "actions for you" }),
			coming_up: region([
				entry({ key: "start", owner: "bid_opening", module: "Bid opening", title: "Supply of network switches", reference: "TND-MOH-2027-042", action: "Start opening", badge: "In 7 days", exact: "25 June, 11:00" }),
				entry({ key: "deadline", owner: "evaluation", module: "Evaluation", title: "Supply of office desks", reference: "TND-MOH-2027-043", action: "Evaluation deadline", badge: "In 13 days", exact: "1 July" }),
			], { count: 2, label: "" }),
			waiting: region([
				entry({ key: "wait", title: "Supply of UPS units", action: "Waiting for Amina Hassan to decide publication", holder: "Accounting Officer", timing: "Waiting 2 days (since 16 June, 15:30)" }),
			], { label: "item you're waiting on" }),
			oversight: region([
				entry({ key: "o1", owner: "evaluation", module: "Evaluation", title: "Supply of office desks", action: "Committee review outstanding", timing: "Outstanding 15 days (since 3 June, 10:00)" }),
				entry({ key: "o2", title: "Supply of IT peripherals", action: "Warranty requirement returned for correction; awaiting correction by Brian Wafula", timing: "Outstanding 2 days (since 16 June, 09:00)" }),
			], { label: "records with outstanding matters" }),
			completed: region([
				entry({ key: "done", title: "Supply of UPS units", sentence: "You approved this Tender package on 16 June 2027, 15:30 EAT. It is awaiting publication authorisation by Amina Hassan." }),
			], { count: 1 }),
		},
	});
}

const mounted = [];

function mountHome() {
	const __ = globalThis.__;
	const wrapper = mount(Home, { attachTo: document.body, global: { mocks: { __, frappe: globalThis.frappe } } });
	mounted.push(wrapper);
	return wrapper;
}

// The visible text, one space between pieces (the components lay text out in separate inline elements).
function textOf(node) {
	const parts = [];
	const walk = (n) => {
		if (n.nodeType === 3) {
			const s = n.textContent.trim();
			if (s) parts.push(s);
		} else if (n.nodeType === 1) n.childNodes.forEach(walk);
	};
	walk(node);
	return parts.join(" ").replace(/\s+/g, " ").trim();
}
const text = (target) => textOf(target.element || target);

afterEach(() => {
	// Every mounted page watches the same resume signal; leave none behind.
	while (mounted.length) mounted.pop().unmount();
});

beforeEach(() => {
	document.body.innerHTML = "";
	vi.clearAllMocks();
	globalThis.__homeEpoch.value = 0;
	globalThis.frappe.set_route = vi.fn();
	globalThis.frappe.route_options = null;
	homeApi.load.mockResolvedValue(charles());
});

describe("Home, HOME-DES-21 (Charles)", () => {
	it("shows the header, the three summary columns in order and the first view of the board", async () => {
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.get('[data-testid="kt-home-title"]').text()).toBe("Good morning, Charles");
		expect(wrapper.get('[data-testid="kt-home-responsibilities"]').text()).toBe("Head of Procurement Function, site-wide");
		expect(wrapper.get('[data-testid="kt-home-updated"]').text()).toBe("Updated 18 June 2027, 10:00 EAT");
		const columns = wrapper.findAll('[data-testid^="kt-home-summary-"]');
		expect(columns.map((c) => c.attributes("data-testid"))).toEqual(["kt-home-summary-my_work", "kt-home-summary-waiting", "kt-home-summary-oversight"]);
		expect(columns.map((c) => text(c))).toEqual(["My work 3 actions for you", "Waiting on others 1 item you're waiting on", "Records you oversee 2 records with outstanding matters"]);
		expect(columns[0].classes()).toContain("is-task");
		expect(columns[1].classes()).not.toContain("is-task");
	});

	it("shows My work rows led by the title, then module and reference, then the action and its timing", async () => {
		const wrapper = mountHome();
		await flushPromises();
		const rows = wrapper.findAll('#my-work [data-testid="kt-home-row"]');
		expect(rows.map((r) => text(r))).toEqual([
			"Clinic equipment requisition Requisitions Authorise requisition Received 2 days ago (16 June, 11:00) Continue",
			"Supply of printers Award TND-MOH-2027-044 Prepare professional opinion Received 2 days ago (16 June, 14:07) Continue",
			"Supply of monitors Award TND-MOH-2027-045 Resolve notice delivery Received yesterday (17 June, 11:00) A required notice is not yet confirmed. Continue",
		]);
		expect(rows[0].find(".kt-home-row-title").text()).toBe("Clinic equipment requisition");
	});

	it("makes only the first Continue primary", async () => {
		const wrapper = mountHome();
		await flushPromises();
		const buttons = wrapper.findAll('[data-testid="kt-home-continue"]');
		expect(buttons.map((b) => b.classes().includes("btn-primary"))).toEqual([true, false, false]);
		expect(buttons.map((b) => b.classes().includes("btn-secondary"))).toEqual([false, true, true]);
	});

	it("shows no Your turn label on ordinary rows, and a callout for a reason", async () => {
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.text()).not.toContain("Your turn");
		expect(wrapper.get('[data-testid="kt-home-reason"]').text()).toBe("A required notice is not yet confirmed.");
	});

	it("shows Coming up with a badge and the exact time, and View record links", async () => {
		const wrapper = mountHome();
		await flushPromises();
		const rows = wrapper.findAll('#coming-up [data-testid="kt-home-row"]');
		expect(rows.map((r) => text(r))).toEqual([
			"Supply of network switches Bid opening TND-MOH-2027-042 Start opening In 7 days 25 June, 11:00 View record",
			"Supply of office desks Evaluation TND-MOH-2027-043 Evaluation deadline In 13 days 1 July View record",
		]);
		expect(rows[0].get(".kt-home-badge").text()).toBe("In 7 days");
		expect(wrapper.findAll('#coming-up button')).toHaveLength(0);
	});

	it("shows the rail in order, with text links and no buttons", async () => {
		const wrapper = mountHome();
		await flushPromises();
		const rail = wrapper.get('[data-testid="kt-home-rail"]');
		expect(rail.findAll("h2").map((h) => h.text())).toEqual(["Waiting on others", "Records you oversee", "Recently completed actions"]);
		expect(rail.findAll(".kt-home-rail-title").map((a) => a.text())).toEqual(["Supply of UPS units", "Supply of office desks", "Supply of IT peripherals", "Supply of UPS units"]);
		expect(text(rail.get("#waiting"))).toBe("Waiting on others Supply of UPS units Waiting for Amina Hassan to decide publication Waiting 2 days (since 16 June, 15:30)");
		expect(text(rail.get("#completed"))).toContain("You approved this Tender package on 16 June 2027, 15:30 EAT. It is awaiting publication authorisation by Amina Hassan.");
		expect(rail.findAll("button")).toHaveLength(0);
	});

	it("does not offer the Procurement Analytics link without an Analytics verdict", async () => {
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.text()).not.toContain("Procurement Analytics");
		const refused = payload({ ...charles(), analytics: { allowed: false, label: "Procurement Analytics", see_all: "See all in Procurement Analytics", route: ["analytics"] } });
		homeApi.load.mockResolvedValue(refused);
		const again = mountHome();
		await flushPromises();
		expect(again.find('[data-testid="kt-home-analytics-link"]').exists()).toBe(false);
	});

	it("offers See all in Procurement Analytics after the oversight rows when the server's verdict permits it (ANL-CHG-001 D14)", async () => {
		homeApi.load.mockResolvedValue(payload({ ...charles(), analytics: { allowed: true, label: "Procurement Analytics", see_all: "See all in Procurement Analytics", route: ["analytics"] } }));
		const wrapper = mountHome();
		await flushPromises();
		const link = wrapper.get('[data-testid="kt-home-analytics-link"]');
		expect(link.text()).toBe("See all in Procurement Analytics");
		expect(link.element.closest('[data-testid="kt-home-region-oversight"]')).not.toBeNull();
		await link.trigger("click");
		expect(globalThis.frappe.set_route).toHaveBeenCalledWith("analytics");
		expect(wrapper.find('[data-testid="kt-home-header-analytics-link"]').exists()).toBe(false); // not a technical reader
	});

	it("opens the owner's route, with its options, when Continue is pressed", async () => {
		const wrapper = mountHome();
		await flushPromises();
		await wrapper.findAll('[data-testid="kt-home-continue"]')[1].trigger("click");
		expect(globalThis.frappe.route_options).toEqual({ tab: "opinion" });
		expect(globalThis.frappe.set_route).toHaveBeenCalledWith("award", "AWD-1");
	});

	it("follows a plain link click through the Desk router, and leaves a modified click to the browser", async () => {
		const wrapper = mountHome();
		await flushPromises();
		const link = wrapper.get("#coming-up .kt-home-link");
		expect(link.attributes("href")).toBe("/app/tenders/TND-1");
		await link.trigger("click");
		expect(globalThis.frappe.set_route).toHaveBeenCalledWith("tenders", "TND-1");
		globalThis.frappe.set_route.mockClear();
		await link.trigger("click", { ctrlKey: true });
		expect(globalThis.frappe.set_route).not.toHaveBeenCalled();
	});

	it("moves focus to the region when a summary column is pressed, and does not read or navigate", async () => {
		const wrapper = mountHome();
		await flushPromises();
		homeApi.load.mockClear();
		await wrapper.get('[data-testid="kt-home-summary-waiting"]').trigger("click");
		expect(document.activeElement.id).toBe("waiting-heading");
		await wrapper.get('[data-testid="kt-home-summary-my_work"]').trigger("click");
		expect(document.activeElement.id).toBe("my-work-heading");
		expect(homeApi.load).not.toHaveBeenCalled();
		expect(globalThis.frappe.set_route).not.toHaveBeenCalled();
	});

	it("has landmarks and a heading order: one h1, region headings are h2", async () => {
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.findAll("h1")).toHaveLength(1);
		expect(wrapper.findAll("section").every((s) => s.attributes("aria-labelledby"))).toBe(true);
		expect(wrapper.get("aside").attributes("aria-label")).toBe("Other work");
	});
});

describe("Home, loading, total failure and denied (HOME-DES-28D, 28E, 28F)", () => {
	it("shows only the heading and 'Loading your work…' while the first read is pending", async () => {
		let release;
		homeApi.load.mockReturnValue(new Promise((resolve) => (release = resolve)));
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.get("h1").text()).toBe("Home");
		expect(wrapper.get('[data-testid="kt-home-loading"]').text()).toBe("Loading your work…");
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
		release(charles());
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-home-loading"]').exists()).toBe(false);
	});

	it("shows 'We could not load your work.' with a primary Try again, and Try again reads again", async () => {
		homeApi.load.mockRejectedValueOnce(new Error("boom"));
		const wrapper = mountHome();
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-home-failed"]'))).toBe("We could not load your work. Try again");
		expect(wrapper.get('[data-testid="kt-home-retry-all"]').classes()).toContain("btn-primary");
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
		await wrapper.get('[data-testid="kt-home-retry-all"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="kt-home-title"]').text()).toBe("Good morning, Charles");
	});

	it("treats the server's total-failure verdict the same way", async () => {
		homeApi.load.mockResolvedValue(payload({ state: "failed" }));
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-home-failed"]').exists()).toBe(true);
	});

	it("shows 'This page is for internal users.' and nothing else for a non-internal user", async () => {
		homeApi.load.mockResolvedValue({ state: "denied" });
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.get("h1").text()).toBe("Home");
		expect(text(wrapper.get('[data-testid="kt-home-denied"]'))).toBe("This page is for internal users.");
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
		expect(wrapper.findAll("button")).toHaveLength(0);
	});
});

describe("Home, region failure (HOME-DES-28B, 28C)", () => {
	function brian() {
		const data = charles();
		data.viewer = { ...data.viewer, first_name: "Brian" };
		data.regions.coming_up = NA();
		data.regions.oversight = NA();
		data.regions.completed = NA();
		data.regions.waiting = region([], { coverage: "unavailable", count: null, total: null, label: "items you're waiting on" });
		return data;
	}

	it("keeps the other regions, shows the region's own message with Try again, and 'Count unavailable' in its column", async () => {
		homeApi.load.mockResolvedValue(brian());
		const wrapper = mountHome();
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-home-summary-waiting"]'))).toBe("Waiting on others Count unavailable items you're waiting on");
		expect(text(wrapper.get("#waiting"))).toBe("Waiting on others We could not load this section. Try again");
		expect(wrapper.findAll('#my-work [data-testid="kt-home-row"]')).toHaveLength(3);
	});

	it("retries one region by reading again and keeps the page meanwhile", async () => {
		homeApi.load.mockResolvedValueOnce(brian());
		const wrapper = mountHome();
		await flushPromises();
		let release;
		homeApi.load.mockReturnValueOnce(new Promise((resolve) => (release = resolve)));
		await wrapper.get('#waiting [data-testid="kt-home-retry"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-home-loading"]').exists()).toBe(false); // no skeleton over a page that has content
		expect(wrapper.get('#waiting [data-testid="kt-home-retry"]').attributes("disabled")).toBeDefined();
		release(charles());
		await flushPromises();
		expect(wrapper.find('#waiting [data-testid="kt-home-failure"]').exists()).toBe(false);
		expect(text(wrapper.get('[data-testid="kt-home-summary-waiting"]'))).toBe("Waiting on others 1 item you're waiting on");
	});

	it("keeps its rows and says some could not be loaded when a region is partial", async () => {
		const data = charles();
		data.regions.waiting = { ...data.regions.waiting, coverage: "partial", count: null, total: null };
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.findAll("#waiting .kt-home-rail-row")).toHaveLength(1);
		expect(wrapper.get("#waiting").text()).toContain("Some work in this section could not be loaded.");
		expect(text(wrapper.get('[data-testid="kt-home-summary-waiting"]'))).toContain("Count unavailable");
	});

	it("shows Coming up's failure inside the main column (28C)", async () => {
		const data = charles();
		data.regions.coming_up = region([], { coverage: "unavailable", count: null, total: null });
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		expect(text(wrapper.get("#coming-up"))).toBe("Coming up We could not load this section. Try again");
	});

	it("shows a retry's own failure when the retry read cannot be made", async () => {
		homeApi.load.mockResolvedValueOnce(brian());
		const wrapper = mountHome();
		await flushPromises();
		homeApi.load.mockRejectedValueOnce(new Error("network"));
		await wrapper.get('#waiting [data-testid="kt-home-retry"]').trigger("click");
		await flushPromises();
		expect(wrapper.get("#waiting").text()).toContain("We could not load this section.");
		expect(wrapper.get('[data-testid="kt-home-title"]').text()).toBe("Good morning, Brian");
	});
});

describe("Home, Show more (HOME-DES-26, 26B)", () => {
	const rows = (from, to) =>
		Array.from({ length: to - from + 1 }, (_, i) =>
			entry({ key: "c" + (from + i), title: "Supply " + (from + i), action: "Respond to clarification", timing: "", destination: dest(["tenders", "T" + (from + i)]), primary: from === 1 && i === 0 })
		);

	function brianEight() {
		const data = payload();
		data.viewer.first_name = "Brian";
		data.regions.my_work = region(rows(1, 5), { count: 6, total: 6, shown: 5, remaining: 1, paged: true, next_cursor: "CUR1", next_count: 1, label: "actions for you" });
		data.regions.waiting = region([], { count: 0, total: 0, label: "items you're waiting on" });
		return data;
	}

	it("shows five rows, 'Showing 5 of 6' and 'Show 1 more'", async () => {
		homeApi.load.mockResolvedValue(brianEight());
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.findAll("#my-work [data-testid='kt-home-row']")).toHaveLength(5);
		expect(wrapper.get('[data-testid="kt-home-showing"]').text()).toBe("Showing 5 of 6");
		expect(wrapper.get('[data-testid="kt-home-show-more"]').text()).toBe("Show 1 more");
		expect(text(wrapper.get('[data-testid="kt-home-summary-my_work"]'))).toBe("My work 6 actions for you");
	});

	it("appends the sixth row in place, leaves the count, focuses the new row and removes the action", async () => {
		homeApi.load.mockResolvedValueOnce(brianEight());
		const wrapper = mountHome();
		await flushPromises();
		homeApi.load.mockResolvedValueOnce({
			state: "ready",
			regions: { my_work: region(rows(6, 6), { count: 6, total: 6, shown: 6, remaining: 0, paged: true, next_cursor: null, next_count: 0 }) },
		});
		await wrapper.get('[data-testid="kt-home-show-more"]').trigger("click");
		await flushPromises();
		expect(homeApi.load).toHaveBeenLastCalledWith(["my_work"], { my_work: "CUR1" });
		const titles = wrapper.findAll("#my-work .kt-home-row-title").map((t) => t.text());
		expect(titles).toEqual(["Supply 1", "Supply 2", "Supply 3", "Supply 4", "Supply 5", "Supply 6"]);
		expect(wrapper.get('[data-testid="kt-home-showing"]').text()).toBe("Showing 6 of 6");
		expect(wrapper.find('[data-testid="kt-home-show-more"]').exists()).toBe(false);
		expect(text(wrapper.get('[data-testid="kt-home-summary-my_work"]'))).toBe("My work 6 actions for you");
		expect(document.activeElement.getAttribute("data-key")).toBe("c6");
		expect(wrapper.get('[data-testid="kt-home-live"]').text()).toBe("Showing 6 of 6");
		expect(wrapper.findAll('[data-testid="kt-home-continue"]').filter((b) => b.classes().includes("btn-primary"))).toHaveLength(1);
	});

	it("keeps the rows and offers Try again when Show more cannot be read", async () => {
		homeApi.load.mockResolvedValueOnce(brianEight());
		const wrapper = mountHome();
		await flushPromises();
		homeApi.load.mockRejectedValueOnce(new Error("boom"));
		await wrapper.get('[data-testid="kt-home-show-more"]').trigger("click");
		await flushPromises();
		expect(wrapper.findAll("#my-work [data-testid='kt-home-row']")).toHaveLength(5);
		expect(text(wrapper.get('[data-testid="kt-home-more-failed"]'))).toBe("Some work in this section could not be loaded. Try again");
		homeApi.load.mockResolvedValueOnce({ state: "ready", regions: { my_work: region(rows(6, 6), { count: 6, total: 6, shown: 6, remaining: 0, paged: true, next_cursor: null, next_count: 0 }) } });
		await wrapper.get('[data-testid="kt-home-more-failed"] button').trigger("click");
		await flushPromises();
		expect(wrapper.findAll("#my-work [data-testid='kt-home-row']")).toHaveLength(6);
		expect(wrapper.find('[data-testid="kt-home-more-failed"]').exists()).toBe(false);
	});
});

describe("Home, placement rules (HOME §5.1 items 7 and 8, §10B.1 items 4A and 5)", () => {
	it("blocked work shows 'Your turn, blocked' and its reason, and with no rail the main column spans all 12 (HOME-DES-25)", async () => {
		const data = payload();
		data.regions.my_work = region([entry({ key: "b", title: "Supply of clinic peripherals", reference: "TND-MOH-2027-040", action: "Respond to clarification", blocked: true, reason: "Issue an addendum before sending this answer.", primary: true, timing: "" })], { label: "action for you" });
		data.regions.waiting = region([], { count: 0, total: 0, label: "items you're waiting on" });
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		const row = wrapper.get('#my-work [data-testid="kt-home-row"]');
		expect(text(row)).toContain("Respond to clarification Your turn, blocked");
		expect(row.get('[data-testid="kt-home-reason"]').text()).toBe("Issue an addendum before sending this answer.");
		expect(wrapper.get('[data-testid="kt-home-main"]').classes()).toContain("is-full");
		expect(wrapper.find("aside").exists()).toBe(false);
		expect(text(wrapper.get('[data-testid="kt-home-summary-my_work"]'))).toBe("My work 1 action for you");
	});

	it("with My work and Coming up both empty, 'Nothing needs your action right now.' leads and oversight moves into the main column (HOME-DES-23)", async () => {
		const data = payload();
		data.viewer = { ...data.viewer, greeting: "Good afternoon", first_name: "Amina", responsibilities: { items: [], line: "Accounting Officer, site-wide" } };
		data.regions.my_work = region([], { count: 0, total: 0, label: "actions for you" });
		data.regions.waiting = region([], { count: 0, total: 0, label: "items you're waiting on" });
		data.regions.oversight = region([entry({ key: "o", owner: "award", module: "Award", title: "Supply and delivery of business laptops", reference: "TND-MOH-2027-033", action: "Award: awaiting professional opinion by Charles Mutiso", timing: "Outstanding today (since 16 June, 14:07)" })], { count: 1, label: "record with outstanding matters" });
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-home-nothing"]'))).toBe("Nothing needs your action right now.");
		expect(wrapper.get('[data-testid="kt-home-main"]').classes()).toContain("is-full");
		expect(wrapper.find("aside").exists()).toBe(false);
		expect(wrapper.find("#my-work").exists()).toBe(false);
		expect(wrapper.find("#coming-up").exists()).toBe(false);
		expect(text(wrapper.get("#oversee"))).toContain("Records you oversee Supply and delivery of business laptops Award TND-MOH-2027-033 Award: awaiting professional opinion by Charles Mutiso");
		expect(wrapper.get("#oversee h2").classes()).toContain("is-main");
		expect(wrapper.findAll('[data-testid="kt-home-summary-my_work"], [data-testid="kt-home-summary-waiting"], [data-testid="kt-home-summary-oversight"]')).toHaveLength(3);
		expect(text(wrapper.get('[data-testid="kt-home-summary-oversight"]'))).toBe("Records you oversee 1 record with outstanding matters");
	});

	it("an oversight row that carries an owner's link shows the dated fact and View report, which opens the owner's own destination (HOME-DES-23, HOME-AC-07)", async () => {
		const data = payload();
		data.regions.my_work = region([], { count: 0, total: 0, label: "actions for you" });
		data.regions.oversight = region([entry({
			key: "o", owner: "award", module: "Award", title: "Supply and delivery of business laptops", reference: "TND-MOH-2027-033", action: "Award: awaiting professional opinion by Charles Mutiso",
			timing: "Outstanding today (since 16 June, 14:07)", fact: "Evaluation report delivered 16 June, 14:07", destination: dest(["award", "AWD-1"]),
			link: { label: "View report", destination: dest(["tenders", "TND-MOH-2027-033", "evaluation", "report"]) },
		})], { count: 1, label: "record with outstanding matters" });
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		const row = wrapper.get('#oversee [data-testid="kt-home-row"]');
		expect(text(row)).toBe("Supply and delivery of business laptops Award TND-MOH-2027-033 Award: awaiting professional opinion by Charles Mutiso Outstanding today (since 16 June, 14:07) Evaluation report delivered 16 June, 14:07 View report");
		expect(row.get('[data-testid="kt-home-view"]').attributes("href")).toBe("/app/tenders/TND-MOH-2027-033/evaluation/report");
		expect(row.get('[data-testid="kt-home-view"]').attributes("aria-label")).toBe("View report: Supply and delivery of business laptops");
	});

	it("a rail row with a link shows the fact and the link under its timing", async () => {
		const data = charles();
		data.regions.oversight.entries[0] = entry({
			key: "o1", owner: "award", module: "Award", title: "Supply of office desks", action: "Awaiting award decision", timing: "Outstanding 2 days (since 16 June, 09:00)",
			fact: "Evaluation report delivered 15 June, 09:30", link: { label: "View report", destination: dest(["tenders", "TND-X", "evaluation", "report"]) },
		});
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		const row = wrapper.findAll('#oversee [data-testid="kt-home-row"]')[0];
		expect(text(row)).toBe("Supply of office desks Awaiting award decision Outstanding 2 days (since 16 June, 09:00) Evaluation report delivered 15 June, 09:30 View report");
		expect(row.get('[data-testid="kt-home-view"]').attributes("href")).toBe("/app/tenders/TND-X/evaluation/report");
	});

	it("shows summary columns only for applicable regions (HOME-DES-22 has no oversight column)", async () => {
		const data = charles();
		data.regions.oversight = NA();
		data.regions.coming_up = NA();
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.findAll('[data-testid^="kt-home-summary-"]')).toHaveLength(2);
		expect(wrapper.find("#oversee").exists()).toBe(false);
	});

	it("omits a region with no entries after a successful read", async () => {
		const data = charles();
		data.regions.completed = region([]);
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.find("#completed").exists()).toBe(false);
	});
});

describe("Home, empty and technical (HOME-DES-28A, 27)", () => {
	it("a successful empty read shows the spot and the sentence, with no summary columns or regions", async () => {
		homeApi.load.mockResolvedValue(payload({ empty: true, summary_visible: false, viewer: { greeting: "Good morning", first_name: "Brian", technical: false, responsibilities: { items: [], line: "Procurement Officer, site-wide" } } }));
		const wrapper = mountHome();
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-home-empty"]'))).toBe("Nothing needs your action right now.");
		expect(wrapper.find(".kt-spot.is-success").exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
		expect(wrapper.findAll("section")).toHaveLength(0);
		expect(wrapper.get('[data-testid="kt-home-responsibilities"]').text()).toBe("Procurement Officer, site-wide");
	});

	it("a technical reader sees the Technical record search link, no counts and no business action", async () => {
		homeApi.load.mockResolvedValue(payload({ empty: true, summary_visible: false, viewer: { greeting: "Good morning", first_name: "Daniel", technical: true, responsibilities: { items: [], line: "Technical Operator, site-wide" } } }));
		const wrapper = mountHome();
		await flushPromises();
		const link = wrapper.get('[data-testid="kt-home-technical-link"]');
		expect(link.text()).toBe("Technical record search");
		await link.trigger("click");
		expect(globalThis.frappe.set_route).toHaveBeenCalledWith("technical-search");
		expect(text(wrapper.get('[data-testid="kt-home-empty-technical"]'))).toBe("Nothing needs your action right now.");
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
		expect(wrapper.findAll("button")).toHaveLength(0);
		expect(wrapper.find(".kt-spot").exists()).toBe(false);
	});

	it("a technical reader with technical work sees those rows, the search link and no counts (FU-HOME-46)", async () => {
		const data = payload({ empty: false, summary_visible: false, viewer: { greeting: "Good morning", first_name: "Daniel", technical: true, responsibilities: { items: [], line: "Technical Operator, site-wide" } } });
		data.regions.my_work = region([entry({ key: "support|SI-1|resolve", owner: "support", module: "Support issues", title: "Resolve evaluation issue for TND-TEST-001", reference: "SI-2027-00001", action: "Repair the failed operation", timing: "Opened 2 days ago (16 June, 11:00)", primary: true, destination: dest(["Form", "Support Issue", "SI-2027-00001"]) })], { label: "action for you" });
		homeApi.load.mockResolvedValue(data);
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-home-technical-link"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
		const row = wrapper.get('#my-work [data-testid="kt-home-row"]');
		expect(text(row)).toBe("Resolve evaluation issue for TND-TEST-001 Support issues SI-2027-00001 Repair the failed operation Opened 2 days ago (16 June, 11:00) Continue");
		await row.get('[data-testid="kt-home-continue"]').trigger("click");
		expect(globalThis.frappe.set_route).toHaveBeenCalledWith("Form", "Support Issue", "SI-2027-00001");
	});

	it("an ordinary user never sees the technical link", async () => {
		const wrapper = mountHome();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-home-technical-link"]').exists()).toBe(false);
	});
});

describe("Home, revalidation in place", () => {
	it("reads again, without a skeleton, when the page is shown again on the same route", async () => {
		const wrapper = mountHome();
		await flushPromises();
		homeApi.load.mockClear();
		let release;
		homeApi.load.mockReturnValueOnce(new Promise((resolve) => (release = resolve)));
		globalThis.__homeEpoch.value += 1;
		await flushPromises();
		expect(homeApi.load).toHaveBeenCalledTimes(1);
		expect(wrapper.find('[data-testid="kt-home-loading"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(true);
		const next = charles();
		next.regions.my_work = region([], { count: 0, total: 0, label: "actions for you" });
		release(next);
		await flushPromises();
		expect(text(wrapper.get('[data-testid="kt-home-summary-my_work"]'))).toBe("My work 0 actions for you");
	});

	it("an older read can never overwrite a newer one", async () => {
		let releaseFirst;
		homeApi.load.mockReturnValueOnce(new Promise((resolve) => (releaseFirst = resolve)));
		const wrapper = mountHome();
		await flushPromises();
		homeApi.load.mockResolvedValueOnce(payload({ empty: true, summary_visible: false }));
		globalThis.__homeEpoch.value += 1;
		await flushPromises();
		releaseFirst(charles());
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-home-empty"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-home-summary"]').exists()).toBe(false);
	});
});

describe("layoutOf", () => {
	it("keeps oversight in the rail while the main column has content", () => {
		const layout = layoutOf(charles());
		expect(layout.main).toEqual(["my_work", "coming_up"]);
		expect(layout.rail).toEqual(["waiting", "oversight", "completed"]);
		expect(layout.railEmpty).toBe(false);
	});

	it("a failed region stays in the layout even with no rows", () => {
		const data = charles();
		data.regions.waiting = region([], { coverage: "unavailable", count: null, total: null });
		expect(layoutOf(data).rail).toContain("waiting");
		expect(layoutOf(data).columns.find((c) => c.region === "waiting").unavailable).toBe(true);
	});
});
