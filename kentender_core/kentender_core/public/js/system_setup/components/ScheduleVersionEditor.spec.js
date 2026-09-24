// CFG-CHG-002 v0.11 §10.9 (C04) — the schedule editor. An administrator may
// change anything about a schedule. What that produces depends on whether the
// schedule could already matter to anyone: one nothing pins and that has not
// taken effect is corrected in place, and any other is replaced by a new
// immutable Version. The server decides which; this screen is told.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({
	getScheduleProfile: vi.fn(),
	registerScheduleProfileVersion: vi.fn(),
	updateScheduleProfile: vi.fn(),
}));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import ScheduleVersionEditor from "./ScheduleVersionEditor.vue";

const MILESTONES = [
	{ milestone: "invitation", label: "Invitation or advertisement", sequence: 1, applies: true, basis: "Statutory", minimum_days: null, maximum_days: null, default_days: null, statutory_reference: "" },
	{ milestone: "bid_opening", label: "Bid opening", sequence: 2, applies: true, basis: "Statutory", minimum_days: 21, maximum_days: null, default_days: 21, statutory_reference: "s.96" },
	{ milestone: "evaluation_completion", label: "Evaluation completion", sequence: 3, applies: true, basis: "Statutory", minimum_days: null, maximum_days: 30, default_days: 30, statutory_reference: "" },
	{ milestone: "award_approval", label: "Tender award approval", sequence: 4, applies: true, basis: "Planning assumption", minimum_days: null, maximum_days: null, default_days: 5, statutory_reference: "" },
	{ milestone: "award_notification", label: "Notification of award", sequence: 5, applies: true, basis: "Planning assumption", minimum_days: null, maximum_days: null, default_days: 2, statutory_reference: "" },
	{ milestone: "contract_signing", label: "Contract signing", sequence: 6, applies: true, basis: "Statutory", minimum_days: 14, maximum_days: null, default_days: 14, statutory_reference: "" },
	{ milestone: "delivery_completion", label: "Delivery or implementation completion", sequence: 7, applies: true, basis: "Source-derived", minimum_days: null, maximum_days: null, default_days: null, statutory_reference: "" },
];

const profile = {
	profile: "SPR-OPEN-TENDER-GOODS-V1",
	profile_name: "Open Tender — goods",
	procurement_method: "Open Tender",
	procurement_category: "Goods",
	procedure: "",
	version_number: 1,
	status: "Active",
	effective_from: "2027-05-01",
	effective_until: "2028-06-30",
	applicability_basis: "Planned invitation date",
	counting_rule: "Calendar days",
	calendar: null,
	estimated_delivery_period_default_days: null,
	verification_status: "Production verification pending",
	source_instrument: "",
	provision: "",
	source_document: "",
	milestones: MILESTONES,
	can_edit: false,
	edit_blocked_reason: "This schedule has already taken effect, so it cannot change. Create a new version instead.",
	expected_version: "2026-09-23 10:00:00",
};

const CALENDARS = [
	{ calendar: "KENYA-V2", calendar_name: "Kenya public holidays", version_number: 2, status: "Active", verification_status: "Verified" },
	{ calendar: "KENYA-V3", calendar_name: "Kenya public holidays", version_number: 3, status: "Active", verification_status: "Production verification pending" },
];

function mountEditor(props = {}) {
	return mount(ScheduleVersionEditor, {
		props: {
			name: "SPR-OPEN-TENDER-GOODS-V1",
			calendars: CALENDARS,
			applicabilityBases: ["Planned invitation date", "Financial year start"],
			verificationStatuses: ["Production verification pending", "Verified"],
			...props,
		},
		global: globalMocks(),
	});
}

async function openEditor(props) {
	const wrapper = mountEditor(props);
	await flushPromises();
	return wrapper;
}

describe("ScheduleVersionEditor", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.getScheduleProfile.mockResolvedValue(profile);
		api.registerScheduleProfileVersion.mockResolvedValue({ profile: "SPR-OPEN-TENDER-GOODS-V2", version_number: 2 });
		api.updateScheduleProfile.mockResolvedValue({ profile: "SPR-OPEN-TENDER-GOODS-V1", version_number: 1 });
	});

	it("opens on the schedule's own values, with every milestone editable", async () => {
		const wrapper = await openEditor();
		expect(wrapper.find('[data-testid="kt-sve-title"]').text()).toBe("Procurement schedule — new version");
		expect(wrapper.find('[data-testid="kt-sve-method"]').text()).toBe("Open Tender");
		expect(wrapper.find('[data-testid="kt-sve-category"]').text()).toBe("Goods");
		expect(wrapper.find('[data-testid="kt-sve-name"]').element.value).toBe("Open Tender — goods");
		expect(wrapper.findAll('[data-testid^="kt-sve-milestone-"]')).toHaveLength(7);
		expect(wrapper.find('[data-testid="kt-sve-default-1"]').element.value).toBe("21");
		// The dialog this replaces offered the day counts and nothing else.
		expect(wrapper.find('[data-testid="kt-sve-counting"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-sve-applies-1"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-sve-delivery"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-sve-basis-1"]').exists()).toBe(true);
	});

	it("offers only a verified calendar to count working days by, and asks for one", async () => {
		const wrapper = await openEditor();
		expect(wrapper.find('[data-testid="kt-sve-calendar"]').exists()).toBe(false);

		await wrapper.find('[data-testid="kt-sve-counting"]').setValue("Working days");
		const options = wrapper.find('[data-testid="kt-sve-calendar"]').findAll("option").map((o) => o.element.value);
		expect(options).toEqual(["", "KENYA-V2"]);
		expect(wrapper.find('[data-testid="kt-sve-blocked"]').text()).toContain("Select a verified working-day calendar");
		expect(wrapper.find('[data-testid="kt-sve-save"]').attributes("disabled")).toBeDefined();
	});

	it("says which milestone is inconsistent instead of letting the server refuse the save", async () => {
		const wrapper = await openEditor();
		await wrapper.find('[data-testid="kt-sve-default-1"]').setValue("7");
		expect(wrapper.find('[data-testid="kt-sve-blocked"]').text()).toBe("Bid opening: the default is below the minimum.");

		await wrapper.find('[data-testid="kt-sve-default-1"]').setValue("21");
		await wrapper.find('[data-testid="kt-sve-default-2"]').setValue("45");
		expect(wrapper.find('[data-testid="kt-sve-blocked"]').text()).toBe("Evaluation completion: the default exceeds the maximum.");

		await wrapper.find('[data-testid="kt-sve-default-2"]').setValue("30");
		await wrapper.find('[data-testid="kt-sve-name"]').setValue("  ");
		expect(wrapper.find('[data-testid="kt-sve-blocked"]').text()).toBe("Give this schedule a name.");
		expect(api.registerScheduleProfileVersion).not.toHaveBeenCalled();
	});

	it("saves a replacement with the whole schedule and the reason for it", async () => {
		const wrapper = await openEditor();
		await wrapper.find('[data-testid="kt-sve-default-3"]').setValue("7");
		await wrapper.find('[data-testid="kt-sve-applies-6"]').setValue(false);
		await wrapper.find('[data-testid="kt-sve-delivery"]').setValue("45");
		await wrapper.find('[data-testid="kt-sve-from"]').setValue("2028-07-01");
		await wrapper.find('[data-testid="kt-sve-reason"]').setValue("Award approval buffer widened after the 2028 review.");
		await wrapper.find('[data-testid="kt-sve-save"]').trigger("click");
		await flushPromises();

		expect(api.updateScheduleProfile).not.toHaveBeenCalled();
		const call = api.registerScheduleProfileVersion.mock.calls[0][0];
		expect(call.procurement_method).toBe("Open Tender");
		expect(call.procurement_category).toBe("Goods");
		expect(call.effective_from).toBe("2028-07-01");
		expect(call.estimated_delivery_period_default_days).toBe(45);
		expect(call.milestones).toHaveLength(7);
		expect(call.milestones[3].default_days).toBe(7);
		expect(call.milestones[6].applies).toBe(false);
		expect(wrapper.emitted("saved")[0]).toEqual(["SPR-OPEN-TENDER-GOODS-V2"]);
		// Starts after the one it came from ends: nothing is replaced (D16).
		expect(call.supersedes_version_ids).toEqual([]);
	});

	it("a replacement whose dates overlap the version it came from declares that version (D16)", async () => {
		const wrapper = await openEditor();
		await wrapper.find('[data-testid="kt-sve-from"]').setValue("2028-01-01");
		await wrapper.find('[data-testid="kt-sve-reason"]').setValue("Award approval buffer widened after the 2028 review.");
		await wrapper.find('[data-testid="kt-sve-save"]').trigger("click");
		await flushPromises();
		expect(api.registerScheduleProfileVersion.mock.calls[0][0].supersedes_version_ids).toEqual(["SPR-OPEN-TENDER-GOODS-V1"]);
	});

	describe("correcting a schedule in place", () => {
		it("changes this Version rather than replacing it, and asks for no reason", async () => {
			const wrapper = await openEditor({ mode: "correct" });
			expect(wrapper.find('[data-testid="kt-sve-title"]').text()).toBe("Procurement schedule — edit schedule");
			expect(wrapper.find('[data-testid="kt-sve-correcting-notice"]').text()).toContain("Once either happens, changing it means a new version");
			expect(wrapper.find('[data-testid="kt-sve-replacement"]').exists()).toBe(false);
			expect(wrapper.find('[data-testid="kt-sve-reason"]').exists()).toBe(false);
			expect(wrapper.find('[data-testid="kt-sve-save"]').text()).toBe("Save changes");
			expect(wrapper.find('[data-testid="kt-sve-save"]').attributes("disabled")).toBeUndefined();

			await wrapper.find('[data-testid="kt-sve-default-3"]').setValue("7");
			await wrapper.find('[data-testid="kt-sve-save"]').trigger("click");
			await flushPromises();

			expect(api.registerScheduleProfileVersion).not.toHaveBeenCalled();
			const call = api.updateScheduleProfile.mock.calls[0][0];
			expect(call.profile).toBe("SPR-OPEN-TENDER-GOODS-V1");
			expect(call.expected_version).toBe("2026-09-23 10:00:00");
			expect(call.milestones[3].default_days).toBe(7);
			expect(call.procurement_method).toBeUndefined();
			expect(wrapper.emitted("saved")[0]).toEqual(["SPR-OPEN-TENDER-GOODS-V1"]);
		});

		it("reports the server's refusal when the schedule froze while it was open", async () => {
			api.updateScheduleProfile.mockRejectedValue(new Error("A plan already uses this schedule, so it cannot change. Create a new version instead."));
			const wrapper = await openEditor({ mode: "correct" });
			await wrapper.find('[data-testid="kt-sve-save"]').trigger("click");
			await flushPromises();
			expect(wrapper.find('[data-testid="kt-sve-error"]').text()).toContain("Create a new version instead");
			expect(wrapper.emitted("saved")).toBeFalsy();
		});
	});

	it("shows the not-available state for a schedule it cannot read", async () => {
		api.getScheduleProfile.mockRejectedValue(new Error("That schedule profile version does not exist."));
		const wrapper = await openEditor({ name: "SPR-NOPE-V9" });
		expect(wrapper.find('[data-testid="kt-sve-load-error"]').text()).toContain("This schedule isn't available to you");
		expect(wrapper.find('[data-testid="kt-sve-save"]').exists()).toBe(false);
	});
});
