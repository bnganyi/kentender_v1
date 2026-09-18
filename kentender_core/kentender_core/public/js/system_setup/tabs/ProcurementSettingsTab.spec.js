// PLN-CHG-001 v1.18 §10.11 C03/C04 — the Procurement settings tab renders the
// server's catalogue and rule Versions, routes sub-views by sub-path and
// shows Forbidden / error states as data, never an empty success.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "../components/spec_helpers.js";

const api = vi.hoisted(() => ({
	get: vi.fn(),
	getMethodProfile: vi.fn(),
	getScheduleProfile: vi.fn(),
	getRegulatoryReferenceVersion: vi.fn(),
	setReminderThresholdDays: vi.fn(),
	addFundingSource: vi.fn(),
	updateFundingSource: vi.fn(),
	deleteFundingSource: vi.fn(),
}));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import ProcurementSettingsTab from "./ProcurementSettingsTab.vue";

function payload(overrides = {}) {
	return {
		outcome: "OK",
		funding_sources: [
			{ name: "Government of Kenya", label: "Government of Kenya", enabled: true, referenced: true, expected_version: "v1" },
			{ name: "Development partner", label: "Development partner", enabled: false, referenced: false, expected_version: "v2" },
		],
		method_profiles: [
			{ profile: "MPR-OPEN-TENDER-V1", procurement_method: "Open Tender", version_number: 1, status: "Active", effective_from: "2027-07-01", effective_until: "2028-06-30", verification_status: "Production verification pending", conditions: [] },
		],
		reference_sets: [
			{
				reference_set: "rs-reservation",
				reference_key: "RESERVATION-RULES",
				reference_kind: "Reservation rules",
				display_name: "Reservation rules",
				has_version: true,
				version: { name: "rv-1", version_number: 3, status: "Active", effective_from: "2027-07-01", effective_until: "2028-06-30", verification_status: "Production verification pending" },
			},
			{
				reference_set: "rs-margins",
				reference_key: "PREFERENCE-MARGINS",
				reference_kind: "Preference margins",
				display_name: "Preference margins",
				has_version: false,
				version: null,
			},
		],
		reference_kinds: ["Method eligibility", "Reservation rules", "Preference margins"],
		schedule_profiles: [
			{ profile: "SPR-OPEN-TENDER-GOODS-V1", profile_name: "Open Tender — goods", procurement_method: "Open Tender", procurement_category: "Goods", version_number: 1, status: "Active", effective_from: "2027-07-01", effective_until: "2028-06-30", verification_status: "Production verification pending", complete: true, gaps: [], milestones: [] },
		],
		reminder_threshold_days: 7,
		verification_statuses: ["Production verification pending", "Fixture-verified — not production law", "Verified"],
		...overrides,
	};
}

async function mountTab(subpath = "") {
	const wrapper = mount(ProcurementSettingsTab, { props: { subpath }, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

describe("ProcurementSettingsTab", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.get.mockResolvedValue(payload());
	});

	it("renders the C03 sections in order: funding sources, procurement rules, schedule profiles, reminders", async () => {
		const wrapper = await mountTab();
		const html = wrapper.html();
		expect(html.indexOf('data-testid="kt-procset-sources"')).toBeLessThan(html.indexOf('data-testid="kt-procset-rules"'));
		expect(html.indexOf('data-testid="kt-procset-rules"')).toBeLessThan(html.indexOf('data-testid="kt-procset-profiles"'));
		expect(html.indexOf('data-testid="kt-procset-profiles"')).toBeLessThan(html.indexOf('data-testid="kt-procset-reminder"'));
		expect(wrapper.find('[data-testid="kt-procset-subnav"]').text()).toContain("Funding sources");
		expect(wrapper.text()).toContain("Add funding source");
	});

	it("funding sources show availability as Yes/No and an Edit link per row", async () => {
		const wrapper = await mountTab();
		const gok = wrapper.find('[data-testid="kt-procset-source-Government of Kenya"]');
		expect(gok.text()).toContain("Yes");
		expect(wrapper.find('[data-testid="kt-procset-source-Development partner"]').text()).toContain("No");
		await gok.find('[data-testid="kt-procset-source-edit-Government of Kenya"]').trigger("click");
		expect(wrapper.emitted("navigate")[0]).toEqual(["source/Government of Kenya"]);
	});

	it("only an unreferenced funding source offers Remove, and confirming it calls the delete API", async () => {
		const wrapper = await mountTab();
		expect(wrapper.find('[data-testid="kt-procset-source-remove-Government of Kenya"]').exists()).toBe(false);
		const removeLink = wrapper.find('[data-testid="kt-procset-source-remove-Development partner"]');
		expect(removeLink.exists()).toBe(true);

		api.deleteFundingSource.mockResolvedValue({ name: "Development partner", deleted: true });
		api.get.mockResolvedValueOnce(payload({ funding_sources: [payload().funding_sources[0]] }));
		await removeLink.trigger("click");
		await flushPromises();
		const dialog = wrapper.find('[data-testid="kt-procset-source-remove-confirm"]');
		expect(dialog.exists()).toBe(true);
		await dialog.find('[data-testid="kt-ou-confirm-accept"]').trigger("click");
		await flushPromises();

		expect(api.deleteFundingSource).toHaveBeenCalledWith("Development partner");
		expect(wrapper.find('[data-testid="kt-procset-source-remove-confirm"]').exists()).toBe(false);
	});

	it("procurement rules list every method profile and reference Version with its source verification", async () => {
		const wrapper = await mountTab();
		const rules = wrapper.find('[data-testid="kt-procset-rules"]');
		expect(rules.text()).toContain("Method eligibility — Open Tender");
		expect(rules.text()).toContain("Reservation rules");
		expect(rules.text()).toContain("1 Jul 2027");
		expect(rules.text()).toContain("30 Jun 2028");
		// §7.3 — a set with no version yet is its own recoverable row, never an
		// empty version row.
		expect(rules.find('[data-testid="kt-procset-rule-noversion-rs-margins"]').text()).toBe("No version saved");
		// §8.1 — the plain result vocabulary, the same on every screen.
		expect(rules.findAll(".kt-status.is-attention").map((s) => s.text())).toEqual([
			"Source check needed",
			"Source check needed",
		]);
		expect(rules.text()).not.toContain("Verified ");
	});

	it("View routes to the rule or profile sub-path; the sub-path selects the view", async () => {
		const wrapper = await mountTab();
		await wrapper.find('[data-testid="kt-procset-rule-view-MPR-OPEN-TENDER-V1"]').trigger("click");
		expect(wrapper.emitted("navigate").at(-1)).toEqual(["rule/MPR-OPEN-TENDER-V1"]);
		await wrapper.find('[data-testid="kt-procset-profile-view-SPR-OPEN-TENDER-GOODS-V1"]').trigger("click");
		expect(wrapper.emitted("navigate").at(-1)).toEqual(["profile/SPR-OPEN-TENDER-GOODS-V1"]);

		api.getMethodProfile.mockResolvedValue({ profile: "MPR-OPEN-TENDER-V1", procurement_method: "Open Tender", version_number: 1, verification_status: "Production verification pending", conditions: [], effective_from: "2027-07-01", effective_until: "2028-06-30" });
		const detail = await mountTab("rule/MPR-OPEN-TENDER-V1");
		expect(detail.find('[data-testid="kt-procset-rule"]').exists()).toBe(true);
		expect(detail.find('[data-testid="kt-procset-sources"]').exists()).toBe(false);
	});

	it("shows the setup Forbidden state as data and the load-error state with Try again", async () => {
		api.get.mockResolvedValueOnce({ outcome: "FORBIDDEN" });
		const forbidden = await mountTab();
		expect(forbidden.find('[data-testid="kt-procset-forbidden"]').text()).toContain("You do not have access to System setup");
		expect(forbidden.find('[data-testid="kt-procset-sources"]').exists()).toBe(false);

		api.get.mockRejectedValueOnce(new Error("boom"));
		const failed = await mountTab();
		expect(failed.find('[data-testid="kt-procset-error"]').exists()).toBe(true);
		expect(failed.find('[data-testid="kt-procset-retry"]').exists()).toBe(true);
	});
});
