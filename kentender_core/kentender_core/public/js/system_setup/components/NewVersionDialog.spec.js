// Create new version — copies the current Version's values, submits one
// register command, never edits in place. Only a schedule profile uses this
// dialog; a method eligibility rule has its own full editor
// (`MethodVersionEditor.spec.js`), because its conditions have to be added
// and removed, not only retyped.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ registerScheduleProfileVersion: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import NewVersionDialog from "./NewVersionDialog.vue";

const current = {
	procurement_method: "Open Tender",
	procurement_category: "Goods",
	profile_name: "Open Tender — goods",
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	milestones: [{ milestone: "bid_opening", label: "Bid opening", sequence: 2, basis: "Statutory", default_days: 21 }],
	estimated_delivery_period_default_days: null,
};

describe("NewVersionDialog", () => {
	beforeEach(() => vi.clearAllMocks());

	it("registers a schedule profile Version from the edited copy", async () => {
		api.registerScheduleProfileVersion.mockResolvedValue({ profile: "SPR-OPEN-TENDER-GOODS-V2", version_number: 2 });
		const wrapper = mount(NewVersionDialog, { props: { current, verificationStatuses: ["Production verification pending", "Verified"] }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-nv-effective-from"]').setValue("2028-07-01");
		await wrapper.find('[data-testid="kt-nv-effective-until"]').setValue("2029-06-30");
		await wrapper.find('[data-testid="kt-nv-confirm"]').trigger("click");
		await flushPromises();
		const call = api.registerScheduleProfileVersion.mock.calls[0][0];
		expect(call.procurement_method).toBe("Open Tender");
		expect(call.effective_from).toBe("2028-07-01");
		expect(call.milestones[0].milestone).toBe("bid_opening");
		expect(wrapper.emitted("registered")).toBeTruthy();
	});

	it("reports a refusal inline and does not report the version as registered", async () => {
		api.registerScheduleProfileVersion.mockRejectedValue(new Error("Milestone bid_opening: the default is below the minimum."));
		const wrapper = mount(NewVersionDialog, { props: { current }, global: globalMocks() });
		await wrapper.find('[data-testid="kt-nv-confirm"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-nv-error"]').text()).toContain("below the minimum");
		expect(wrapper.emitted("registered")).toBeFalsy();
	});
});
