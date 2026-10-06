// BDS-CHG-001 v0.8 §10.2 BDS-DES-01 — structure at both frames, the empty
// state, and a filter change: the caller's own selection is sent to the
// server and written to the URL with replace (no new history entry).
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";
import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import AvailableTendersScreen from "./AvailableTendersScreen.vue";

const ROW = { reference: "TND-MOH-2027-033", title: "Supply and delivery of business laptops", procuring_entity: "Ministry of Health", method: "Open Tender", reservation: "Youth", submission_deadline_label: "12 Jun 2027, 11:00 EAT", href: "/tenders/TND-MOH-2027-033" };
const OPTIONS = {
	method: [{ value: "", label: "All methods" }, { value: "Open Tender", label: "Open Tender" }],
	reservation: [{ value: "", label: "All categories" }, { value: "Youth", label: "Youth" }],
	closing: [{ value: "open", label: "Open Tenders" }, { value: "closed", label: "Closed or cancelled" }, { value: "all", label: "All Tenders" }],
};
const LIST = { rows: [ROW], count_text: "1 available Tender", empty_text: "", applied: {}, options: OPTIONS };
const EMPTY = { rows: [], count_text: "", empty_text: "No Tenders match these filters.", applied: {}, options: OPTIONS };

function fakePortal(result = LIST) {
	const route = ref({ path: "/tenders", segments: ["tenders"], query: {} });
	const portal = {
		call: vi.fn(async () => result),
		go: vi.fn(),
		setTitle: vi.fn(),
		createSequenceGuard,
		createCommandRunner,
		createScreenCache,
		useRoute: () => ({ route, go: (...args) => portal.go(...args), epoch: ref(0) }),
	};
	return portal;
}

function render(initial, portal = fakePortal()) {
	return { wrapper: mount(AvailableTendersScreen, { props: { initial }, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } }), portal };
}

afterEach(() => {
	globalThis.__narrow = false;
});

describe("AvailableTendersScreen", () => {
	it("draws the board's table at 1440 with the title, reference beneath and View Tender", () => {
		const { wrapper, portal } = render(LIST);
		expect(portal.call).not.toHaveBeenCalled(); // first paint from the server payload
		expect(wrapper.find("h1.kt-page-title").text()).toBe("Available Tenders");
		expect(wrapper.findAll("thead th").map((th) => th.text())).toEqual(["Tender", "Procuring Entity", "Method", "Reservation", "Submission deadline", "Action"]);
		const cells = wrapper.findAll("tbody td");
		expect(cells[0].find(".kt-label").text()).toBe("TND-MOH-2027-033");
		expect(cells[5].find("a").attributes("href")).toBe("/tenders/TND-MOH-2027-033");
		expect(wrapper.find('[data-testid="kt-pager-count"]').text()).toBe("1 available Tender");
		expect(wrapper.text()).not.toMatch(/Start bid/);
	});

	it("draws labelled cards at 390 instead of the table", () => {
		globalThis.__narrow = true;
		const { wrapper } = render(LIST);
		expect(wrapper.find("table").exists()).toBe(false);
		expect(wrapper.findAll(".bds-card-fact .kt-label").map((l) => l.text())).toEqual(["Procuring Entity", "Method", "Reservation", "Submission deadline"]);
		expect(wrapper.find(".kt-filter-bar").classes()).toContain("bds-filter-stack");
	});

	it("shows the empty state with Clear filters and no table", () => {
		const { wrapper } = render(EMPTY);
		expect(wrapper.find("table").exists()).toBe(false);
		expect(wrapper.find('[data-testid="bds-tenders-empty"]').text()).toContain("No Tenders match these filters.");
		expect(wrapper.find('[data-testid="bds-tenders-empty"] button').text()).toBe("Clear filters");
	});

	it("sends the caller's selection and replaces the URL on a filter change", async () => {
		const { wrapper, portal } = render(LIST, fakePortal(EMPTY));
		await wrapper.find("#bds-filter-closing").setValue("all");
		await flushPromises();
		expect(portal.call).toHaveBeenCalledWith("kentender_procurement.bid_submission.api.get_available_tenders", { search: "", method: "", reservation: "", closing: "all" });
		expect(portal.go).toHaveBeenCalledWith("/tenders", { replace: true, query: { search: "", method: "", reservation: "", closing: "all" }, keepFocus: true });
		expect(wrapper.find("#bds-filter-closing").element.value).toBe("all");
		expect(wrapper.find('[data-testid="bds-tenders-empty"]').exists()).toBe(true);
	});

	it("loads when there is no first payload and shows a load failure inline", async () => {
		const portal = fakePortal();
		portal.call = vi.fn(async () => {
			throw new Error("The service could not complete this request. Your saved work is unchanged. Try again.");
		});
		const { wrapper } = render(null, portal);
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-load-failure"]').text()).toContain("Try again");
	});
});
