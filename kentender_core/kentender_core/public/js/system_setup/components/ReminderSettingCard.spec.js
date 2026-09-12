// C04-eligibility-reminder — the reminder threshold card.
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
		expect(wrapper.find(".kt-card-title").text()).toBe("Approaching milestone threshold");
		expect(wrapper.find('[data-testid="kt-reminder-days"]').element.value).toBe("7");
		expect(wrapper.text()).toContain("Operational reminder period; not a statutory procurement deadline.");
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
});
