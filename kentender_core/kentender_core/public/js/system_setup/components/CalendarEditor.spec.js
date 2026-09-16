// CFG-CHG-002 v0.11 §10.9 (C04 "calendar") — the working-day calendar: an
// immutable version, holiday rows editable only while unsaved, and a
// successor rather than an edit.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({
	getBusinessDayCalendar: vi.fn(),
	registerBusinessDayCalendarVersion: vi.fn(),
}));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import CalendarEditor from "./CalendarEditor.vue";

const SAVED = {
	calendar: "KENYA-PUBLIC-HOLIDAYS-V1",
	calendar_name: "Kenya public holidays",
	version_number: 1,
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	weekend_days: ["Saturday", "Sunday"],
	holidays: [{ holiday_date: "2027-12-12", holiday_name: "Jamhuri Day" }],
	verification_status: "Production verification pending",
	source_instrument: "Public Holidays Act (Cap. 110)",
};

describe("CalendarEditor", () => {
	beforeEach(() => vi.clearAllMocks());

	it("creating: weekend days default to Saturday and Sunday, holiday rows are addable, and the version is registered", async () => {
		api.registerBusinessDayCalendarVersion.mockResolvedValue({ calendar: "C1" });
		const wrapper = mount(CalendarEditor, { props: { creating: true }, global: globalMocks() });

		expect(wrapper.find('[data-testid="kt-cal-weekend-Saturday"]').element.checked).toBe(true);
		expect(wrapper.find('[data-testid="kt-cal-weekend-Sunday"]').element.checked).toBe(true);
		expect(wrapper.find('[data-testid="kt-cal-weekend-Monday"]').element.checked).toBe(false);
		expect(wrapper.find('[data-testid="kt-cal-save"]').attributes("disabled")).toBeDefined();

		await wrapper.find('[data-testid="kt-cal-name"]').setValue("Kenya public holidays");
		await wrapper.find('[data-testid="kt-cal-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-cal-add-holiday"]').trigger("click");
		await wrapper.find('[data-testid="kt-cal-holiday-date-0"]').setValue("2027-12-12");
		await wrapper.find('[data-testid="kt-cal-holiday-name-0"]').setValue("Jamhuri Day");
		await wrapper.find('[data-testid="kt-cal-save"]').trigger("click");
		await flushPromises();

		expect(api.registerBusinessDayCalendarVersion.mock.calls[0][0]).toMatchObject({
			calendar_name: "Kenya public holidays",
			effective_from: "2027-07-01",
			weekend_days: ["Saturday", "Sunday"],
			holidays: [{ holiday_date: "2027-12-12", holiday_name: "Jamhuri Day" }],
		});
		expect(wrapper.emitted("saved")).toBeTruthy();
	});

	it("a saved version is read-only with no row controls, and Create new version opens the successor editor", async () => {
		api.getBusinessDayCalendar.mockResolvedValue(SAVED);
		const wrapper = mount(CalendarEditor, { props: { name: SAVED.calendar }, global: globalMocks() });
		await flushPromises();

		expect(wrapper.find('[data-testid="kt-cal-name-ro"]').text()).toBe("Kenya public holidays");
		expect(wrapper.find('[data-testid="kt-cal-weekend-ro"]').text()).toBe("Saturday, Sunday");
		expect(wrapper.find('[data-testid="kt-cal-verification"]').text()).toBe("Source check needed");
		// Add row / Remove row belong to the unsaved editor only.
		expect(wrapper.find('[data-testid="kt-cal-add-holiday"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-cal-name"]').exists()).toBe(false);

		await wrapper.find('[data-testid="kt-cal-new-version"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-cal-name"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-cal-add-holiday"]').exists()).toBe(true);
		// A successor states its own period rather than inheriting the predecessor's.
		expect(wrapper.find('[data-testid="kt-cal-from"]').element.value).toBe("");
	});
});
