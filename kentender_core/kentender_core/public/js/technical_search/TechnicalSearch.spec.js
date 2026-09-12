// AUTH-ADR-001 §10 — Technical record search screen: the verdict is resolved
// once on mount (empty-query search: 404 → Forbidden, 200 → Empty), then a
// typed search shows No match or the results table, whose Open opens the
// resolver's own route — alongside (never instead of) the browser layer.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./data/technicalSearchApi.js", () => ({
	technicalSearchApi: {
		search: vi.fn(async () => []),
		resolve: vi.fn(async () => null),
	},
}));

import TechnicalSearch from "./TechnicalSearch.vue";
import { technicalSearchApi } from "./data/technicalSearchApi.js";

function globalMocks() {
	const __ = (text, args) =>
		String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
	return { mocks: { __, frappe: { set_route: vi.fn() } } };
}

function mountScreen() {
	return mount(TechnicalSearch, { global: globalMocks() });
}

beforeEach(() => {
	vi.clearAllMocks();
	technicalSearchApi.search.mockResolvedValue([]);
});

describe("TechnicalSearch", () => {
	it("shows the Empty state once the initial verdict call succeeds with no query typed", async () => {
		const wrapper = mountScreen();
		await flushPromises();
		expect(technicalSearchApi.search).toHaveBeenCalledWith("", 25);
		expect(wrapper.find('[data-testid="kt-ts-empty"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-ts-forbidden"]').exists()).toBe(false);
	});

	it("shows the Forbidden state when the initial verdict call comes back 404", async () => {
		const err = new Error("Not found");
		err.httpStatus = 404;
		technicalSearchApi.search.mockRejectedValueOnce(err);
		const wrapper = mountScreen();
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-ts-forbidden"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-ts-forbidden"]').text()).toContain(
			"You do not have access to Technical record search"
		);
	});

	it("shows No match for a query with zero results", async () => {
		const wrapper = mountScreen();
		await flushPromises();
		technicalSearchApi.search.mockResolvedValueOnce([]);
		await wrapper.find('[data-testid="kt-ts-input"]').setValue("NDS-NONE-0001");
		await wrapper.find('[data-testid="kt-ts-search"]').trigger("click");
		await flushPromises();
		const nomatch = wrapper.find('[data-testid="kt-ts-nomatch"]');
		expect(nomatch.exists()).toBe(true);
		expect(nomatch.text()).toContain('No record matches "NDS-NONE-0001"');
	});

	it("renders result rows and opens the resolver's own route on Open", async () => {
		const wrapper = mountScreen();
		await flushPromises();
		const row = {
			reference: "NDS-MOH-2027-0001",
			record_type: "Departmental Need",
			doctype: "Departmental Need",
			name: "NDS-0001",
			title: "Laboratory reagents",
			status: "Submitted",
			route: ["departmental-needs", "NDS-0001"],
		};
		technicalSearchApi.search.mockResolvedValueOnce([row]);
		await wrapper.find('[data-testid="kt-ts-input"]').setValue("NDS-MOH-2027-0001");
		await wrapper.find('[data-testid="kt-ts-search"]').trigger("click");
		await flushPromises();

		const rows = wrapper.findAll('[data-testid="kt-ts-row"]');
		expect(rows).toHaveLength(1);
		expect(rows[0].text()).toContain("NDS-MOH-2027-0001");
		expect(rows[0].text()).toContain("Departmental Need");
		expect(rows[0].text()).toContain("Laboratory reagents");
		expect(rows[0].text()).toContain("Submitted");

		globalThis.frappe.set_route = vi.fn();
		await rows[0].find('[data-testid="kt-ts-open"]').trigger("click");
		expect(globalThis.frappe.set_route).toHaveBeenCalledWith("departmental-needs", "NDS-0001");
	});

	it("submits the search on Enter in the input", async () => {
		const wrapper = mountScreen();
		await flushPromises();
		technicalSearchApi.search.mockResolvedValueOnce([]);
		await wrapper.find('[data-testid="kt-ts-input"]').setValue("REQ-NONE-0001");
		await wrapper.find('[data-testid="kt-ts-input"]').trigger("keydown.enter");
		await flushPromises();
		expect(technicalSearchApi.search).toHaveBeenCalledWith("REQ-NONE-0001", 25);
	});
});
