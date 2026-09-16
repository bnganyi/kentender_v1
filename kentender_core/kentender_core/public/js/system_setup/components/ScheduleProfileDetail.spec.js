// C04 — a schedule profile Version, read-only.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ getScheduleProfile: vi.fn(), registerScheduleProfileVersion: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import ScheduleProfileDetail from "./ScheduleProfileDetail.vue";

const rows = [
	["invitation", "Invitation or advertisement", null, "Statutory"],
	["bid_opening", "Bid opening", 21, "Statutory"],
	["evaluation_completion", "Evaluation completion", 30, "Statutory"],
	["award_approval", "Tender award approval", 5, "Planning assumption"],
	["award_notification", "Notification of award", 2, "Planning assumption"],
	["contract_signing", "Contract signing", 14, "Statutory"],
	["delivery_completion", "Delivery or implementation completion", null, "Source-derived"],
];
const profile = {
	profile: "SPR-OPEN-TENDER-GOODS-V1",
	profile_name: "Open Tender — goods",
	procurement_method: "Open Tender",
	procedure: "Planning example",
	procurement_category: "Goods",
	version_number: 1,
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	counting_rule: "Calendar days",
	estimated_delivery_period_default_days: null,
	verification_status: "Production verification pending",
	complete: true,
	gaps: [],
	milestones: rows.map(([milestone, label, def, basis], i) => ({ milestone, label, sequence: i + 1, applies: true, counting_rule: "Calendar days", minimum_days: null, maximum_days: null, default_days: def, basis })),
};

describe("ScheduleProfileDetail", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.getScheduleProfile.mockResolvedValue(profile);
	});

	it("renders the C04 header facts, the seven milestone rows with verification-required bounds and the completeness notice", async () => {
		const wrapper = mount(ScheduleProfileDetail, { props: { name: "SPR-OPEN-TENDER-GOODS-V1" }, global: globalMocks() });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-profile-title"]').text()).toBe("Open Tender — goods");
		expect(wrapper.findAll(".kt-procset-meta .kt-label").map((l) => l.text())).toEqual(["Name", "Which date determines the rule to use?", "Method", "Procedure", "Version", "Applies"]);
		// §10.9 keeps the milestones and the intervals between them as two
		// separate tables.
		expect(wrapper.findAll("thead th").map((h) => h.text())).toEqual([
			"Milestone",
			"Order",
			"Applies",
			"Role in this schedule",
			"From",
			"To",
			"Days counted",
			"Minimum status",
			"Maximum status",
			"Default days",
			"Default basis",
		]);
		// Seven milestones, and the six intervals between them.
		expect(wrapper.findAll('[data-testid^="kt-procset-milestone-"]').length).toBe(7);
		expect(wrapper.findAll('[data-testid^="kt-procset-interval-"]').length).toBe(6);
		// Days and their basis describe the interval that closes at a
		// milestone, so they are read from the interval row.
		const award = wrapper.find('[data-testid="kt-procset-interval-award_approval"]');
		expect(award.text()).toContain("Planning assumption");
		expect(award.findAll("td")[5].text()).toBe("5");
		const bid = wrapper.find('[data-testid="kt-procset-interval-bid_opening"]');
		expect(bid.text()).toContain("Verification required");
		expect(bid.findAll("td")[4].text()).toBe("—");
		expect(wrapper.find('[data-testid="kt-procset-profile-delivery-default"]').text()).toBe("Not set");
		expect(wrapper.find('[data-testid="kt-procset-profile-notice"]').text()).toBe("This profile cannot support Plan submission until its required rules and sources are complete.");
		expect(wrapper.findAll("input").length).toBe(0);
	});

	it("a Verified, complete profile shows no notice; Create new version opens the dialog with the milestone rows", async () => {
		api.getScheduleProfile.mockResolvedValueOnce({ ...profile, verification_status: "Verified" });
		const wrapper = mount(ScheduleProfileDetail, { props: { name: "SPR-OPEN-TENDER-GOODS-V1", verificationStatuses: ["Verified"] }, global: globalMocks() });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-profile-notice"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-milestone-bid_opening"]').text()).toContain("Calculated milestone");
		await wrapper.find('[data-testid="kt-procset-profile-new-version"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-nv-milestones"]').findAll(".kt-procset-row").length).toBe(7);
		expect(wrapper.find('[data-testid="kt-nv-profile-name"]').element.value).toBe("Open Tender — goods");
	});
});
