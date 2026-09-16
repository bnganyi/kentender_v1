// CFG-CHG-002 v0.11 §10.10 (Reminders.dc.html) — the reminder threshold card.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ setReminderThresholdDays: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import ReminderSettingCard from "./ReminderSettingCard.vue";

describe("ReminderSettingCard", () => {
	beforeEach(() => vi.clearAllMocks());

	it("shows the threshold with its helper and saves only a changed whole number", async () => {
		api.setReminderThresholdDays.mockResolvedValue({ approaching_milestone_threshold_days: 10 });
		const wrapper = mount(ReminderSettingCard, { props: { days: 7 }, global: globalMocks() });
		expect(wrapper.find(".kt-card-title").text()).toBe("Reminders");
		expect(wrapper.find("label").text()).toBe("Remind users this many days before a milestone");
		expect(wrapper.find('[data-testid="kt-reminder-days"]').element.value).toBe("7");
		expect(wrapper.text()).toContain("Unit: Calendar days");
		expect(wrapper.text()).toContain("This changes reminder timing, not procurement deadlines.");
		expect(wrapper.text()).toContain("Use 0 to begin reminders on the milestone date; overdue reminders still apply.");
		expect(wrapper.find('[data-testid="kt-reminder-save"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-reminder-days"]').setValue("ten");
		expect(wrapper.find('[data-testid="kt-reminder-save"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-reminder-days"]').setValue("10");
		await wrapper.find('[data-testid="kt-reminder-save"]').trigger("click");
		await flushPromises();
		expect(api.setReminderThresholdDays).toHaveBeenCalledWith(10);
		expect(wrapper.find('[data-testid="kt-reminder-success"]').text()).toBe("Changes saved.");
		expect(wrapper.emitted("saved")).toBeTruthy();
	});

	it("a value outside 0-365 names the range and refuses the save", async () => {
		const wrapper = mount(ReminderSettingCard, { props: { days: 7 }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-reminder-days"]').setValue("366");
		expect(wrapper.find('[data-testid="kt-reminder-range-error"]').text()).toBe("Enter a whole number from 0 to 365.");
		expect(wrapper.find('[data-testid="kt-reminder-save"]').attributes("disabled")).toBeDefined();

		// 0 is legitimate: reminders begin on the milestone date.
		await wrapper.find('[data-testid="kt-reminder-days"]').setValue("0");
		expect(wrapper.find('[data-testid="kt-reminder-range-error"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-reminder-save"]').attributes("disabled")).toBeUndefined();
	});
});
