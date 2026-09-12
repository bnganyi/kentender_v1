// Create new version — copies the current Version's values, submits one
// register command, never edits in place.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ registerMethodProfileVersion: vi.fn(), registerScheduleProfileVersion: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import NewVersionDialog from "./NewVersionDialog.vue";

describe("NewVersionDialog", () => {
	beforeEach(() => vi.clearAllMocks());

	it("registers a method profile Version from the edited copy and reports a refusal inline", async () => {
		api.registerMethodProfileVersion.mockResolvedValue({ profile: "MPR-OPEN-TENDER-V2", version_number: 2 });
		const current = { procurement_method: "Open Tender", effective_from: "2027-07-01", effective_until: "2028-06-30", verification_status: "Production verification pending", conditions: [{ condition_id: "G-VALUE", kind: "Known fact", description: "x", procurement_category: "Goods", maximum_amount: 0 }] };
		const wrapper = mount(NewVersionDialog, { props: { mode: "method", current, verificationStatuses: ["Production verification pending", "Verified"] }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-nv-effective-from"]').setValue("2028-07-01");
		await wrapper.find('[data-testid="kt-nv-effective-until"]').setValue("2029-06-30");
		await wrapper.find('[data-testid="kt-nv-confirm"]').trigger("click");
		await flushPromises();
		const call = api.registerMethodProfileVersion.mock.calls[0][0];
		expect(call.procurement_method).toBe("Open Tender");
		expect(call.effective_from).toBe("2028-07-01");
		expect(call.conditions[0].condition_id).toBe("G-VALUE");
		expect(wrapper.emitted("registered")).toBeTruthy();

		api.registerScheduleProfileVersion.mockRejectedValue(new Error("Milestone bid_opening: the default is below the minimum."));
		const schedule = mount(NewVersionDialog, {
			props: { mode: "schedule", current: { procurement_method: "Open Tender", procurement_category: "Goods", profile_name: "Open Tender — goods", effective_from: "2027-07-01", milestones: [{ milestone: "invitation", label: "Invitation", sequence: 1, basis: "Statutory" }], estimated_delivery_period_default_days: null } },
			global: globalMocks(),
		});
		await schedule.find('[data-testid="kt-nv-confirm"]').trigger("click");
		await flushPromises();
		expect(schedule.find('[data-testid="kt-nv-error"]').text()).toContain("below the minimum");
		expect(schedule.emitted("registered")).toBeFalsy();
	});
});
