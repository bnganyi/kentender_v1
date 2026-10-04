// CFG-CHG-002 v0.14 §10.9 (C04 #calendar, #calendar-detail, #calendar-version,
// #calendar-history; tracker CFG14-5F) — the working-day calendar: a saved
// version read-only with its actions, a new calendar, a successor with what
// it replaces and why (D16), a correction while the server allows (D15), and
// its usage and history.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({
	getBusinessDayCalendar: vi.fn(),
	registerBusinessDayCalendarVersion: vi.fn(),
	updateBusinessDayCalendar: vi.fn(),
	listVerificationHistory: vi.fn(),
}));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import CalendarEditor from "./CalendarEditor.vue";
import CalendarDetail from "./CalendarDetail.vue";
import CalendarHistory from "./CalendarHistory.vue";

const SAVED = {
	calendar: "KENYA-PUBLIC-HOLIDAYS-V1",
	calendar_name: "Kenya public holidays",
	version_number: 1,
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	weekend_days: ["Saturday", "Sunday"],
	holidays: [{ holiday_date: "2027-12-12", holiday_name: "Jamhuri Day", source_reference: "Public Holidays Act s.2" }],
	verification_status: "Production verification pending",
	source_instrument: "Public Holidays Act (Cap. 110)",
	can_edit: false,
	recorded_at: "2026-09-12 10:00:00",
	recorded_by: "Administrator",
	supersedes_version_ids: [],
};

async function mountIt(component, props) {
	const wrapper = mount(component, { props, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

describe("CalendarDetail", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.getBusinessDayCalendar.mockResolvedValue(SAVED);
	});

	it("is read-only: the board's facts, holidays with their source evidence, the read-only state and the four actions", async () => {
		const wrapper = await mountIt(CalendarDetail, { name: "KENYA-PUBLIC-HOLIDAYS-V1" });
		expect(wrapper.find("h3").text()).toBe("Working-day calendar");
		expect(wrapper.findAll(".kt-meta-row")[0].findAll(".kt-label").map((l) => l.text())).toEqual([
			"Calendar name", "Version", "Applies from", "Applies until", "Weekend days", "Source check",
		]);
		expect(wrapper.find('[data-testid="kt-cal-holidays"]').text()).toContain("Public Holidays Act s.2");
		expect(wrapper.findAll("input")).toHaveLength(0);
		expect(wrapper.find('[data-testid="kt-cal-readonly"]').text()).toBe("This version is read-only. Create a new version to change it.");
		expect(wrapper.find('[data-testid="kt-cal-edit"]').exists()).toBe(false);
		for (const [id, event] of [["kt-cal-new-version", "new-version"], ["kt-cal-check-sources", "check-sources"], ["kt-cal-history", "history"]]) {
			await wrapper.find(`[data-testid="${id}"]`).trigger("click");
			expect(wrapper.emitted(event), event).toHaveLength(1);
		}
	});

	it("offers Edit calendar, and no read-only state, only while the server allows correction", async () => {
		api.getBusinessDayCalendar.mockResolvedValue({ ...SAVED, can_edit: true });
		const wrapper = await mountIt(CalendarDetail, { name: "KENYA-PUBLIC-HOLIDAYS-V1" });
		expect(wrapper.find('[data-testid="kt-cal-readonly"]').exists()).toBe(false);
		await wrapper.find('[data-testid="kt-cal-edit"]').trigger("click");
		expect(wrapper.emitted("edit")).toHaveLength(1);
	});
});

describe("CalendarEditor", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.getBusinessDayCalendar.mockResolvedValue(SAVED);
	});

	it("create: Saturday and Sunday by default, holiday rows with their source evidence, Save calendar version", async () => {
		api.registerBusinessDayCalendarVersion.mockResolvedValue({ calendar: "C1" });
		const wrapper = await mountIt(CalendarEditor, { mode: "create" });
		expect(wrapper.find("h3").text()).toBe("Working-day calendar");
		expect(wrapper.find('[data-testid="kt-cal-weekend-Saturday"]').element.checked).toBe(true);
		expect(wrapper.find('[data-testid="kt-cal-weekend-Monday"]').element.checked).toBe(false);
		expect(wrapper.find('[data-testid="kt-cal-save"]').text()).toBe("Save calendar version");
		expect(wrapper.find('[data-testid="kt-cal-save"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-cal-name"]').setValue("County holidays");
		await wrapper.find('[data-testid="kt-cal-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-cal-add-holiday"]').trigger("click");
		await wrapper.find('[data-testid="kt-cal-holiday-date-0"]').setValue("2027-10-20");
		await wrapper.find('[data-testid="kt-cal-holiday-name-0"]').setValue("Mashujaa Day");
		await wrapper.find('[data-testid="kt-cal-holiday-source-0"]').setValue("Public Holidays Act s.2");
		await wrapper.find('[data-testid="kt-cal-save"]').trigger("click");
		await flushPromises();
		const sent = api.registerBusinessDayCalendarVersion.mock.calls[0][0];
		expect(sent).toMatchObject({ calendar_name: "County holidays", supersedes_version_ids: [] });
		expect(sent.holidays).toEqual([{ holiday_date: "2027-10-20", holiday_name: "Mashujaa Day", source_reference: "Public Holidays Act s.2" }]);
		expect(wrapper.emitted("saved")[0]).toEqual(["C1"]);
	});

	it("version: starts without dates, says what it replaces only when the dates overlap, and sends the reason (D16)", async () => {
		api.registerBusinessDayCalendarVersion.mockResolvedValue({ calendar: "KENYA-PUBLIC-HOLIDAYS-V2" });
		const wrapper = await mountIt(CalendarEditor, { mode: "version", name: "KENYA-PUBLIC-HOLIDAYS-V1" });
		expect(wrapper.find("h3").text()).toBe("Working-day calendar — new version");
		expect(wrapper.find('[data-testid="kt-cal-name"]').attributes("disabled")).toBeDefined();
		expect(wrapper.find('[data-testid="kt-cal-from"]').element.value).toBe("");
		await wrapper.find('[data-testid="kt-cal-from"]').setValue("2029-07-01");
		expect(wrapper.find('[data-testid="kt-cal-replaces"]').element.value).toBe("None — these dates do not overlap Version 1");
		await wrapper.find('[data-testid="kt-cal-from"]').setValue("2028-01-01");
		expect(wrapper.find('[data-testid="kt-cal-replaces"]').element.value).toBe("Version 1");
		await wrapper.find('[data-testid="kt-cal-reason"]').setValue("Gazetted holidays added.");
		await wrapper.find('[data-testid="kt-cal-save"]').trigger("click");
		await flushPromises();
		expect(api.registerBusinessDayCalendarVersion.mock.calls[0][0]).toMatchObject({
			supersedes_version_ids: ["KENYA-PUBLIC-HOLIDAYS-V1"],
			change_reason: "Gazetted holidays added.",
		});
		expect(wrapper.find('[data-testid="kt-cal-save"]').text()).toBe("Save new version");
	});

	it("correct: keeps the saved dates, says why it may change in place, and saves through the update command", async () => {
		api.getBusinessDayCalendar.mockResolvedValue({ ...SAVED, can_edit: true, expected_version: "v1" });
		api.updateBusinessDayCalendar.mockResolvedValue({ calendar: "KENYA-PUBLIC-HOLIDAYS-V1" });
		const wrapper = await mountIt(CalendarEditor, { mode: "correct", name: "KENYA-PUBLIC-HOLIDAYS-V1" });
		expect(wrapper.find('[data-testid="kt-cal-from"]').element.value).toBe("2027-07-01");
		expect(wrapper.find('[data-testid="kt-cal-correcting-notice"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-cal-reason"]').exists()).toBe(false);
		await wrapper.find('[data-testid="kt-cal-save"]').trigger("click");
		await flushPromises();
		expect(api.updateBusinessDayCalendar.mock.calls[0][0]).toMatchObject({ calendar: "KENYA-PUBLIC-HOLIDAYS-V1", expected_version: "v1" });
		expect(api.registerBusinessDayCalendarVersion).not.toHaveBeenCalled();
	});

	it("a refused save is the server's sentence as a notice; the entries stay", async () => {
		api.registerBusinessDayCalendarVersion.mockRejectedValue(new Error("Each holiday needs a distinct date."));
		const wrapper = await mountIt(CalendarEditor, { mode: "create" });
		await wrapper.find('[data-testid="kt-cal-name"]').setValue("County holidays");
		await wrapper.find('[data-testid="kt-cal-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-cal-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-rule-error"]').text()).toBe("Each holiday needs a distinct date.");
		expect(wrapper.find('[data-testid="kt-cal-name"]').element.value).toBe("County holidays");
	});
});

describe("CalendarHistory", () => {
	it("shows this calendar's versions, its checks and usage, with a View per version", async () => {
		api.getBusinessDayCalendar.mockResolvedValue(SAVED);
		api.listVerificationHistory.mockResolvedValue([]);
		const wrapper = await mountIt(CalendarHistory, {
			name: "KENYA-PUBLIC-HOLIDAYS-V1",
			calendarVersions: [SAVED, { ...SAVED, calendar: "OTHER-V1", calendar_name: "Other" }],
		});
		expect(wrapper.find("h3").text()).toBe("Working-day calendar — usage and history");
		expect(wrapper.findAll('[data-testid^="kt-sc-version-view-"]')).toHaveLength(1);
		expect(wrapper.find('[data-testid="kt-sc-version-1"]').text()).toContain("Administrator");
		await wrapper.find('[data-testid="kt-sc-version-view-1"]').trigger("click");
		expect(wrapper.emitted("view-version")[0]).toEqual(["KENYA-PUBLIC-HOLIDAYS-V1"]);
	});
});
