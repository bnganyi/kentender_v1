// C04 — a schedule profile Version, read-only.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ getScheduleProfile: vi.fn(), registerScheduleProfileVersion: vi.fn(), setVersionValidity: vi.fn() }));
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
	// Frozen by default: the rule's two halves are exercised in the service
	// tests; here the screen only has to show what the server decided.
	can_edit: false,
	edit_blocked_reason: "This schedule has already taken effect, so it cannot change. Create a new version instead.",
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
	valid: false,
	can_set_validity: true,
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
		// The fixture's periods are complete, so the one thing standing in the
		// way is that nobody has marked it valid — said once, with the action
		// beside it rather than a sentence naming neither problem.
		expect(wrapper.find('[data-testid="kt-procset-profile-notice"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-profile-validity-notice"]').text()).toBe("This schedule is not marked valid, so a plan using it cannot be submitted.");
		expect(wrapper.findAll("input").length).toBe(0);
	});

	it("a Verified, complete profile shows no notice, and Create new version asks the parent for the editor", async () => {
		api.getScheduleProfile.mockResolvedValueOnce({ ...profile, verification_status: "Verified" });
		const wrapper = mount(ScheduleProfileDetail, { props: { name: "SPR-OPEN-TENDER-GOODS-V1", verificationStatuses: ["Verified"] }, global: globalMocks() });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-profile-notice"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-profile-validity-notice"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-milestone-bid_opening"]').text()).toContain("Calculated milestone");
		await wrapper.find('[data-testid="kt-procset-profile-new-version"]').trigger("click");
		expect(wrapper.emitted("new-version")).toHaveLength(1);
		// The detail stays a read-only view: no dialog opens over it.
		expect(wrapper.findAll("input").length).toBe(0);
	});

	it("offers Edit schedule only while the server says the schedule can still be corrected", async () => {
		// The fixture is frozen, so a change costs a new Version.
		const frozen = mount(ScheduleProfileDetail, { props: { name: "SPR-OPEN-TENDER-GOODS-V1", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(frozen.find('[data-testid="kt-procset-profile-edit"]').exists()).toBe(false);
		expect(frozen.find('[data-testid="kt-procset-profile-new-version"]').exists()).toBe(true);

		api.getScheduleProfile.mockResolvedValueOnce({ ...profile, can_edit: true, edit_blocked_reason: "" });
		const editable = mount(ScheduleProfileDetail, { props: { name: "SPR-OPEN-TENDER-GOODS-V1", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		await editable.find('[data-testid="kt-procset-profile-edit"]').trigger("click");
		expect(editable.emitted("edit-schedule")).toHaveLength(1);
	});

	it("shows the not-available state, and does not take the panel down, when the schedule cannot be read", async () => {
		// The title renders above the loading/error branches; dereferencing a
		// schedule that failed to load threw there and blanked the whole panel.
		api.getScheduleProfile.mockRejectedValueOnce(new Error("That schedule profile version does not exist."));
		const wrapper = mount(ScheduleProfileDetail, { props: { name: "SPR-GONE-V9", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-profile-error"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-procset-profile-title"]').text()).toBe("Procurement schedule");
		expect(wrapper.find('[data-testid="kt-procset-profile-edit"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-profile-new-version"]').exists()).toBe(false);
	});

	it("marks the schedule valid from the detail, in force or not", async () => {
		api.setVersionValidity.mockResolvedValue({ name: "SPR-OPEN-TENDER-GOODS-V1", valid: true, changed: true });
		const wrapper = mount(ScheduleProfileDetail, { props: { name: "SPR-OPEN-TENDER-GOODS-V1", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		const mark = wrapper.find('[data-testid="kt-procset-profile-validity"]');
		expect(mark.text()).toBe("Mark as valid");

		api.getScheduleProfile.mockResolvedValueOnce({ ...profile, valid: true, verification_status: "Verified" });
		await mark.trigger("click");
		await flushPromises();
		expect(api.setVersionValidity).toHaveBeenCalledWith({ doctype: "Procedure Schedule Profile", name: "SPR-OPEN-TENDER-GOODS-V1", valid: true });
		expect(wrapper.find('[data-testid="kt-procset-profile-validity-notice"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-profile-validity"]').text()).toBe("Remove valid mark");
	});
});
