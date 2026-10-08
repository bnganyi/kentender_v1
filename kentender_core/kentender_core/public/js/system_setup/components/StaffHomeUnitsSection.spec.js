// AUTH-ADR-001 v1.12 AUTH-DES-10 / AUTH-DES-11 and CFG-CHG-002 v0.19 §7, §11.1:
// the Staff home units tab — Not recorded is shown as such, a row opens the
// dialog, a save sends the row's own token and key and re-reads the register,
// a stale token reloads, and a refusal or failure is never an empty register.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ list: vi.fn(), set: vi.fn() }));
vi.mock("../data/staffHomeUnitApi.js", () => ({ staffHomeUnitApi: api, newIdempotencyKey: () => "home-unit-test-key" }));

import StaffHomeUnitsSection from "./StaffHomeUnitsSection.vue";

const UNITS = [{ value: "OU-1", label: "Ministry of Health › Finance" }, { value: "OU-2", label: "Ministry of Health › ICT" }];
const ROWS = [
	{ user: "peter@x.test", full_name: "Peter Mugo", state: "Recorded", organisation_unit: "OU-2", unit_name: "ICT", unit_status: "Active", token: "t1" },
	{ user: "esther@x.test", full_name: "Esther Muthoni", state: "Not recorded", organisation_unit: "", unit_name: "", unit_status: "", token: "t2" },
];

beforeEach(() => {
	vi.clearAllMocks();
	api.list.mockResolvedValue({ outcome: "OK", rows: ROWS, total: 2, units: UNITS });
	api.set.mockResolvedValue({ ok: true });
});

const mountIt = async () => {
	const wrapper = mount(StaffHomeUnitsSection, { global: globalMocks() });
	await flushPromises();
	return wrapper;
};

describe("the Staff home units register", () => {
	it("shows each person's home unit and Not recorded, with the action for each", async () => {
		const wrapper = await mountIt();
		expect(wrapper.find('[data-testid="kt-home-unit-peter@x.test"]').text()).toBe("ICT");
		expect(wrapper.find('[data-testid="kt-home-unit-esther@x.test"]').text()).toBe("Not recorded");
		expect(wrapper.find('[data-testid="kt-home-edit-peter@x.test"]').text()).toBe("Change");
		expect(wrapper.find('[data-testid="kt-home-edit-esther@x.test"]').text()).toBe("Set home unit");
		const headers = wrapper.findAll("th").map((h) => h.text());
		expect(headers).toEqual(["Staff member", "Home organisation unit", "Action"]);
	});

	it("filters to Not recorded through the server, and says so when everyone has one", async () => {
		const wrapper = await mountIt();
		api.list.mockResolvedValue({ outcome: "OK", rows: [], total: 0, units: UNITS });
		await wrapper.find('[data-testid="kt-home-filter"]').setValue("not-recorded");
		await flushPromises();
		expect(api.list).toHaveBeenLastCalledWith({ search: "", notRecorded: true });
		expect(wrapper.find('[data-testid="kt-home-empty"]').text()).toContain("Every staff member has a home unit recorded.");
	});

	it("marks a unit that has become inactive", async () => {
		api.list.mockResolvedValue({ outcome: "OK", rows: [{ ...ROWS[0], unit_status: "Inactive" }], total: 1, units: UNITS });
		const wrapper = await mountIt();
		expect(wrapper.find('[data-testid="kt-home-unit-peter@x.test"]').text()).toBe("ICT Inactive");
	});

	it("never presents a refusal or a failure as an empty register", async () => {
		api.list.mockResolvedValue({ outcome: "FORBIDDEN" });
		let wrapper = await mountIt();
		expect(wrapper.find('[data-testid="kt-home-forbidden"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-home-table"]').exists()).toBe(false);
		api.list.mockRejectedValue(new Error("boom"));
		wrapper = await mountIt();
		expect(wrapper.find('[data-testid="kt-home-error"]').text()).toContain("Staff members could not be loaded");
		expect(wrapper.find('[data-testid="kt-home-empty"]').exists()).toBe(false);
	});
});

describe("the Set home unit dialog", () => {
	it("opens for a person with no unit as Set home unit, and saves with the row's own token", async () => {
		const wrapper = await mountIt();
		await wrapper.find('[data-testid="kt-home-edit-esther@x.test"]').trigger("click");
		expect(wrapper.find("#kt-home-unit-title").text()).toBe("Set home unit");
		expect(wrapper.find('[data-testid="kt-home-unit-clear"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-home-unit-person"]').text()).toBe("Esther Muthoni · esther@x.test");
		expect(wrapper.find('[data-testid="kt-home-unit-save"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-home-unit-select"]').setValue("OU-1");
		await wrapper.find('[data-testid="kt-home-unit-save"]').trigger("click");
		await flushPromises();
		expect(api.set).toHaveBeenCalledWith("esther@x.test", "OU-1", "t2", "home-unit-test-key");
		expect(api.list).toHaveBeenCalledTimes(2); // the register is re-read from the server after the command
		expect(wrapper.find('[data-testid="kt-home-unit-dialog"]').exists()).toBe(false);
	});

	it("opens a recorded person as Change home unit with a Clear action that sends no unit", async () => {
		const wrapper = await mountIt();
		await wrapper.find('[data-testid="kt-home-edit-peter@x.test"]').trigger("click");
		expect(wrapper.find("#kt-home-unit-title").text()).toBe("Change home unit");
		await wrapper.find('[data-testid="kt-home-unit-clear"]').trigger("click");
		await flushPromises();
		expect(api.set).toHaveBeenCalledWith("peter@x.test", "", "t1", "home-unit-test-key");
	});

	it("keeps the dialog open with the server's message, and reloads when the row has changed", async () => {
		api.set.mockRejectedValue(new Error("This information has changed since you opened it."));
		const wrapper = await mountIt();
		await wrapper.find('[data-testid="kt-home-edit-esther@x.test"]').trigger("click");
		await wrapper.find('[data-testid="kt-home-unit-select"]').setValue("OU-2");
		await wrapper.find('[data-testid="kt-home-unit-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-home-unit-error"]').text()).toContain("changed since you opened it");
		expect(api.list).toHaveBeenCalledTimes(2);
	});
});
