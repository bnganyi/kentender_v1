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
import { legacyToRoute } from "../data/routes.js";

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
		procurement_categories: ["Goods", "Works", "Services"],
		condition_kinds: ["Known fact", "Declaration"],
		cumulative_bases: ["None", "Per request", "Funds allocated"],
		method_applicability_bases: ["Planned invitation date", "Financial year start"],
		...overrides,
	};
}

// Tests still name views by the tab's internal view names; the tab now
// receives the parsed §9 route the root derives from the link.
async function mountTab(subpath = "") {
	const route = legacyToRoute("procurement-settings", subpath);
	const wrapper = mount(ProcurementSettingsTab, { props: { route }, global: globalMocks() });
	await flushPromises();
	return wrapper;
}

describe("ProcurementSettingsTab", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.get.mockResolvedValue(payload());
	});

	it("each section is its own view behind the section links; with no section named, Funding sources opens", async () => {
		const wrapper = await mountTab();
		const links = wrapper.findAll('[data-testid="kt-procset-subnav"] a');
		// Tender formats is deferred this cycle, so it has no link (D11).
		// CFG-CHG-002 v0.16 §10.10A: Supplier portal follows Reminders (CFG16-AC-001).
		expect(links.map((a) => a.text())).toEqual(["Funding sources", "Procurement rules", "Procurement schedules", "Reminders", "Supplier portal"]);
		expect(links[0].attributes("aria-current")).toBe("page");
		expect(links[0].classes()).toContain("is-active");
		expect(wrapper.find('[data-testid="kt-procset-sources"]').exists()).toBe(true);
		for (const other of ["kt-procset-rules", "kt-procset-profiles", "kt-procset-calendars", "kt-procset-reminder", "kt-procset-supplier-portal"]) {
			expect(wrapper.find(`[data-testid="${other}"]`).exists(), other).toBe(false);
		}
		await links[1].trigger("click");
		expect(wrapper.emitted("navigate").at(-1)).toEqual(["procurement-rules"]);

		const rules = await mountTab("procurement-rules");
		expect(rules.find('[data-testid="kt-procset-rules"]').exists()).toBe(true);
		expect(rules.find('[data-testid="kt-procset-sources"]').exists()).toBe(false);
		expect(rules.find('[data-testid="kt-procset-link-procurement-rules"]').attributes("aria-current")).toBe("page");

		// Working-day calendars open inside Procurement schedules.
		const schedules = await mountTab("schedule-profiles");
		expect(schedules.find('[data-testid="kt-procset-profiles"]').exists()).toBe(true);
		expect(schedules.find('[data-testid="kt-procset-calendars"]').exists()).toBe(true);
		const reminders = await mountTab("reminders");
		expect(reminders.find('[data-testid="kt-procset-reminder"]').exists()).toBe(true);
	});

	it("the board's funding-source list: heading, description, Add, and the three columns", async () => {
		const wrapper = await mountTab();
		const list = wrapper.find('[data-testid="kt-procset-sources"]');
		expect(list.find("h3").text()).toBe("Funding sources");
		expect(list.find("p.card-body").text()).toBe("Maintain the sources used in procurement budgets.");
		expect(list.find('[data-testid="kt-procset-source-add"]').text()).toBe("Add funding source");
		expect(list.findAll("th").map((th) => th.text())).toEqual(["Name", "Available for new selection", "Action"]);
		// No budget amount, reason or approval controls (§10.5).
		expect(list.text()).not.toMatch(/amount|reason|approv/i);
	});

	it("an empty catalogue is its own centred state with the board's copy and Add", async () => {
		api.get.mockResolvedValue(payload({ funding_sources: [] }));
		const wrapper = await mountTab();
		const empty = wrapper.find('[data-testid="kt-procset-sources-empty"]');
		expect(empty.text()).toBe("No funding sources yetAdd the sources used by this site's procurement budgets.Add funding source");
		expect(wrapper.find('[data-testid="kt-procset-sources"] table').exists()).toBe(false);
		await empty.find("button").trigger("click");
		expect(wrapper.emitted("navigate").at(-1)).toEqual(["new-source"]);
	});

	it("add and edit open the dialog over the list; Cancel returns to the section, and a save re-reads it", async () => {
		const adding = await mountTab("new-source");
		expect(adding.find('[data-testid="kt-procset-sources"]').exists()).toBe(true);
		expect(adding.find('[data-testid="kt-procset-source-editor"] .kt-dialog-title').text()).toBe("Add funding source");
		await adding.find('[data-testid="kt-fs-cancel"]').trigger("click");
		expect(adding.emitted("navigate").at(-1)).toEqual(["funding-sources"]);

		const editing = await mountTab("source/Development partner");
		expect(editing.find('[data-testid="kt-fs-name"]').element.value).toBe("Development partner");
		api.updateFundingSource.mockResolvedValue({ name: "Development partner", enabled: true });
		await editing.find('[data-testid="kt-fs-enabled-yes"] input').trigger("change");
		const reads = api.get.mock.calls.length;
		await editing.find('[data-testid="kt-fs-save"]').trigger("click");
		await flushPromises();
		expect(api.updateFundingSource).toHaveBeenCalledWith("Development partner", { label: "Development partner", enabled: true }, "v2");
		expect(api.get.mock.calls.length).toBeGreaterThan(reads);
		expect(editing.emitted("navigate").at(-1)).toEqual(["funding-sources"]);

		// Focus returns to the Edit link that opened the dialog.
		const returning = await mountTab();
		document.body.appendChild(returning.element);
		const edit = returning.find('[data-testid="kt-procset-source-edit-Development partner"]');
		edit.element.focus();
		await edit.trigger("click");
		await returning.setProps({ route: legacyToRoute("procurement-settings", "source/Development partner") });
		await flushPromises();
		expect(returning.find('[data-testid="kt-procset-source-editor"]').exists()).toBe(true);
		await returning.setProps({ route: legacyToRoute("procurement-settings", "funding-sources") });
		await flushPromises();
		expect(document.activeElement).toBe(returning.find('[data-testid="kt-procset-source-edit-Development partner"]').element);
		returning.unmount();

		// A link to a source that does not exist opens no dialog.
		const missing = await mountTab("source/Nope");
		expect(missing.find('[data-testid="kt-procset-source-editor"]').exists()).toBe(false);
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

	it("an older list read that answers late never overwrites a newer one (Remove right after closing the dialog)", async () => {
		// Regression (24 Sep 2026, browser): closing the dialog starts a quiet
		// re-read; a Remove confirmed before it answered started a second one.
		// The first answered last and put the removed source back on screen.
		const wrapper = await mountTab("source/Development partner");
		let answerStale;
		api.get.mockImplementationOnce(() => new Promise((resolve) => (answerStale = resolve)));
		await wrapper.setProps({ route: legacyToRoute("procurement-settings", "funding-sources") });
		await flushPromises();

		api.deleteFundingSource.mockResolvedValue({ name: "Development partner", deleted: true });
		api.get.mockResolvedValueOnce(payload({ funding_sources: [payload().funding_sources[0]] }));
		await wrapper.find('[data-testid="kt-procset-source-remove-Development partner"]').trigger("click");
		await wrapper.find('[data-testid="kt-procset-source-remove-confirm"] [data-testid="kt-ou-confirm-accept"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-source-Development partner"]').exists()).toBe(false);

		answerStale(payload());
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-source-Development partner"]').exists()).toBe(false);
	});

	it("procurement rules list every method profile and reference Version with its source verification", async () => {
		const wrapper = await mountTab("procurement-rules");
		const rules = wrapper.find('[data-testid="kt-procset-rules"]');
		expect(rules.text()).toContain("Method eligibility — Open Tender");
		expect(rules.text()).toContain("Reservation rules");
		expect(rules.text()).toContain("1 Jul 2027");
		expect(rules.text()).toContain("30 Jun 2028");
		// §7.3 — a set with no version yet is its own recoverable row, never an
		// empty version row.
		const card = rules.find('[data-testid="kt-procset-rule-noversion-rs-margins"]');
		expect(card.text()).toBe("No version savedRulePreference marginsAdd first version");
		// The table lists saved versions only, with "Details" beside "Source check".
		expect(rules.find('[data-testid="kt-procset-rule-rs-margins"]').exists()).toBe(false);
		expect(rules.findAll("th").map((th) => th.text())).toEqual(["Rule", "Applies from", "Applies until", "Version", "Source check", "Details", "Action"]);
		await card.find('[data-testid="kt-procset-rule-first-version-rs-margins"]').trigger("click");
		expect(wrapper.emitted("navigate").at(-1)).toEqual(["new-rule-version/rs-margins"]);
		// §8.1 — the plain result vocabulary, the same on every screen.
		expect(rules.findAll(".kt-status.is-attention").map((s) => s.text())).toEqual([
			"Not marked valid",
			"Not marked valid",
		]);
		expect(rules.text()).not.toContain("Verified ");
	});

	it("View routes to the rule or profile sub-path; the sub-path selects the view", async () => {
		const wrapper = await mountTab("procurement-rules");
		await wrapper.find('[data-testid="kt-procset-rule-view-MPR-OPEN-TENDER-V1"]').trigger("click");
		expect(wrapper.emitted("navigate").at(-1)).toEqual(["rule/MPR-OPEN-TENDER-V1"]);
		const schedules = await mountTab("schedule-profiles");
		await schedules.find('[data-testid="kt-procset-profile-view-SPR-OPEN-TENDER-GOODS-V1"]').trigger("click");
		expect(schedules.emitted("navigate").at(-1)).toEqual(["profile/SPR-OPEN-TENDER-GOODS-V1"]);

		api.getMethodProfile.mockResolvedValue({ profile: "MPR-OPEN-TENDER-V1", procurement_method: "Open Tender", version_number: 1, verification_status: "Production verification pending", conditions: [], effective_from: "2027-07-01", effective_until: "2028-06-30" });
		const detail = await mountTab("rule/MPR-OPEN-TENDER-V1");
		expect(detail.find('[data-testid="kt-procset-rule"]').exists()).toBe(true);
		expect(detail.find('[data-testid="kt-procset-sources"]').exists()).toBe(false);
	});

	it("sends a method rule's new version to its own editor, and a reference rule's to the reference form", async () => {
		const version = { profile: "MPR-OPEN-TENDER-V1", procurement_method: "Open Tender", version_number: 1, verification_status: "Production verification pending", conditions: [], effective_from: "2027-07-01", effective_until: "2028-06-30" };
		api.getMethodProfile.mockResolvedValue(version);
		const detail = await mountTab("rule/MPR-OPEN-TENDER-V1");
		await detail.find('[data-testid="kt-procset-rule-new-version"]').trigger("click");
		expect(detail.emitted("navigate").at(-1)).toEqual(["new-method-version/MPR-OPEN-TENDER-V1"]);

		api.getRegulatoryReferenceVersion.mockResolvedValue({ name: "rv-1", reference_kind: "Reservation rules", version_number: 3, verification_status: "Production verification pending", payload: {}, effective_from: "2027-07-01", effective_until: "2028-06-30" });
		const reference = await mountTab("rule/rv-1");
		await reference.find('[data-testid="kt-procset-rule-new-version"]').trigger("click");
		expect(reference.emitted("navigate").at(-1)).toEqual(["new-rule-version/rv-1"]);
	});

	it("the method editor sub-path opens the editor on that Version, with the server's vocabularies", async () => {
		api.getMethodProfile.mockResolvedValue({
			profile: "MPR-OPEN-TENDER-V1",
			procurement_method: "Open Tender",
			version_number: 1,
			verification_status: "Production verification pending",
			applicability_basis: "Planned invitation date",
			effective_from: "2027-07-01",
			effective_until: "2028-06-30",
			conditions: [{ condition_id: "G-VALUE", kind: "Known fact", description: "No fixed maximum for goods.", procurement_category: "Goods", minimum_amount: 0, maximum_amount: 0, cumulative_basis: "Funds allocated", mandatory: true, required_evidence: "", authorisation_actor: "", authorisation_stage: "", statutory_reference: "" }],
		});
		const wrapper = await mountTab("new-method-version/MPR-OPEN-TENDER-V1");
		const editor = wrapper.find('[data-testid="kt-procset-method-editor"]');
		expect(editor.exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-mve-id-0"]').element.value).toBe("G-VALUE");
		expect(wrapper.find('[data-testid="kt-mve-basis-0"]').findAll("option").map((o) => o.element.value)).toEqual(["None", "Per request", "Funds allocated"]);
		// The tab's own list is not rendered underneath the editor.
		expect(wrapper.find('[data-testid="kt-procset-sources"]').exists()).toBe(false);
	});

	it("cancelling a rule's new version returns to that rule; cancelling Add rule returns to the list", async () => {
		api.getRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-1", reference_set: "rs-reservation", reference_kind: "Reservation rules", version_number: 3, payload: {} });
		const version = await mountTab("new-rule-version/rv-1");
		await version.find('[data-testid="kt-rule-cancel"]').trigger("click");
		expect(version.emitted("navigate").at(-1)).toEqual(["rule/rv-1"]);
		const adding = await mountTab("new-rule");
		await adding.find('[data-testid="kt-rule-cancel"]').trigger("click");
		expect(adding.emitted("navigate").at(-1)).toEqual(["procurement-rules"]);
	});

	it("a direct link to a method rule's new version never asks for a reference version while the list is still loading", async () => {
		// Regression (24 Sep 2026): before the list arrived, the tab could not
		// tell a method rule from a reference rule, treated MPR-… as a
		// reference, and the server answered "That reference version does not exist."
		api.getRegulatoryReferenceVersion.mockClear();
		api.getMethodProfile.mockResolvedValue({ profile: "MPR-OPEN-TENDER-V1", procurement_method: "Open Tender", version_number: 1, conditions: [] });
		const wrapper = await mountTab("new-method-version/MPR-OPEN-TENDER-V1");
		expect(api.getRegulatoryReferenceVersion).not.toHaveBeenCalled();
		expect(wrapper.find('[data-testid="kt-procset-method-editor"]').exists()).toBe(true);
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
