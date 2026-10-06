// C03-detail — a referenced rule Version, read-only, with Create new version.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ getMethodProfile: vi.fn(), getRegulatoryReferenceVersion: vi.fn(), registerMethodProfileVersion: vi.fn(), setVersionValidity: vi.fn(), renameRegulatoryReference: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import RuleVersionDetail from "./RuleVersionDetail.vue";

const profile = {
	profile: "MPR-OPEN-TENDER-V1",
	procurement_method: "Open Tender",
	version_number: 1,
	status: "Active",
	effective_from: "2027-07-01",
	effective_until: "2028-06-30",
	applicability_basis: "Planned invitation date",
	verification_status: "Production verification pending",
	source_instrument: "Public Procurement and Asset Disposal Regulations — source verification pending",
	provision: "Verification required",
	source_document: "",
	can_edit: false,
	valid: false,
	can_set_validity: true,
	edit_blocked_reason: "This rule has already taken effect, so it cannot change. Create a new version instead.",
	conditions: [
		{ condition_id: "G-VALUE", kind: "Known fact", description: "No fixed maximum for goods.", procurement_category: "Goods", maximum_amount: 0, cumulative_basis: "Funds allocated", required_evidence: "", authorisation_actor: "", authorisation_stage: "" },
	],
};

describe("RuleVersionDetail", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.getMethodProfile.mockResolvedValue(profile);
	});

	it("renders the board's saved detail: heading, the six facts in one row, the four groups, the identifier", async () => {
		const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-rule-title"]').text()).toBe("Method eligibility — Open Tender");
		expect(wrapper.find('[data-testid="kt-procset-rule-version"]').text()).toBe("1");
		const labels = wrapper.findAll('[data-testid="kt-procset-rule-card"] .kt-label').map((l) => l.text());
		// §10.6's saved detail: the summary facts, then the four supporting
		// groups (rule details, applicability, sources, usage).
		expect(labels).toEqual([
			"Rule kind",
			"Version",
			"Applies from",
			"Applies until",
			"Source check",
			"Details",
			"Method",
			"Category",
			"Currency",
			"Reason for this version",
			"Which date determines the rule to use?",
			"Entity applicability",
			"County applicability",
			"Source instrument",
			"Edition",
			"Provisions",
			"Source document",
			"Interpretation",
			"Rule identifier",
		]);
		expect(wrapper.findAll(".kt-section > h6").map((h) => h.text())).toEqual([
			"Rule details",
			"When this rule applies",
			"Sources and interpretation",
			"Usage and history",
		]);
		expect(wrapper.text()).toContain("1 Jul 2027");
		expect(wrapper.text()).toContain("Not attached");
		expect(wrapper.find('[data-testid="kt-procset-rule-verification"]').text()).toBe("Not marked valid");
		expect(wrapper.find('[data-testid="kt-procset-rule-values"]').text()).toContain("No fixed maximum for goods.");
		// A rule with a values table lays its groups out full width.
		expect(wrapper.find(".kt-procset-rule-groups").classes()).toContain("has-values");
		expect(wrapper.findAll("input").length).toBe(0);
	});

	it("offers Edit rule only while the server says the rule can still be corrected", async () => {
		// Frozen: the fixture carries can_edit false, so the only way to change
		// the rule is a new version.
		const frozen = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(frozen.find('[data-testid="kt-procset-rule-edit"]').exists()).toBe(false);
		expect(frozen.find('[data-testid="kt-procset-rule-new-version"]').exists()).toBe(true);
		// C03BC #states — the frozen version says it is read-only, with the way on.
		expect(frozen.find('[data-testid="kt-procset-rule-readonly"]').text()).toBe("This version is read-only. Create a new version to change it.Create new version");
		await frozen.find('[data-testid="kt-procset-rule-readonly-new"]').trigger("click");
		expect(frozen.emitted("new-version")).toHaveLength(1);

		api.getMethodProfile.mockResolvedValue({ ...profile, can_edit: true, edit_blocked_reason: "" });
		const editable = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(editable.find('[data-testid="kt-procset-rule-readonly"]').exists()).toBe(false);
		await editable.find('[data-testid="kt-procset-rule-edit"]').trigger("click");
		expect(editable.emitted("edit-rule")).toHaveLength(1);
	});

	it("Create new version asks the parent for the editor rather than editing anything here; a masked record shows the not-available state", async () => {
		const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: ["Production verification pending", "Verified"] }, global: globalMocks() });
		await flushPromises();
		await wrapper.find('[data-testid="kt-procset-rule-new-version"]').trigger("click");
		expect(wrapper.emitted("new-version")).toHaveLength(1);
		// The detail stays a read-only view of the immutable Version: no
		// dialog opens over it and nothing on it becomes editable.
		expect(wrapper.find('[data-testid="kt-procset-new-version"]').exists()).toBe(false);
		expect(wrapper.findAll("input").length).toBe(0);

		api.getMethodProfile.mockRejectedValueOnce(new Error("That method profile version does not exist."));
		const masked = mount(RuleVersionDetail, { props: { name: "MPR-NOPE-V9", kind: "method" }, global: globalMocks() });
		await flushPromises();
		expect(masked.find('[data-testid="kt-procset-rule-error"]').text()).toContain("This record isn't available to you");
	});

	it("states once that the rule is not marked valid, and offers the mark beside it", async () => {
		api.setVersionValidity.mockResolvedValue({ name: "MPR-OPEN-TENDER-V1", valid: true, changed: true });
		const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		// The two duplicates are gone: the badge over the conditions, and the
		// notice that blamed "rule details and source checks" without naming one.
		expect(wrapper.find('[data-testid="kt-procset-rule-incomplete"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-rule-incomplete-notice"]').text()).toBe(
			"This rule is not marked valid, so a plan using it cannot be submitted."
		);
		expect(wrapper.text()).not.toContain("Required conditions not yet completed");
		expect(wrapper.text()).not.toContain("Source check needed");

		const mark = wrapper.find('[data-testid="kt-procset-rule-validity"]');
		expect(mark.text()).toBe("Mark as valid");
		api.getMethodProfile.mockResolvedValue({ ...profile, valid: true, verification_status: "Verified" });
		await mark.trigger("click");
		await flushPromises();
		expect(api.setVersionValidity).toHaveBeenCalledWith({ doctype: "Procurement Method Profile", name: "MPR-OPEN-TENDER-V1", valid: true });
		// Re-read from the server, so the screen shows what was actually stored.
		expect(wrapper.find('[data-testid="kt-procset-rule-incomplete-notice"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-procset-rule-validity"]').text()).toBe("Remove valid mark");
	});

	it("a reference rule: its own name heads it, missing details are named, and Edit rule name renames without leaving", async () => {
		api.getRegulatoryReferenceVersion.mockResolvedValue({
			reference: "rv-1",
			reference_set: "rs-res",
			reference_key: "RESERVATION-RULES",
			reference_kind: "Reservation rules",
			display_name: "Reservation rules",
			version_number: 1,
			effective_from: "2027-07-01",
			effective_until: "2028-06-30",
			verification_status: "Production verification pending",
			payload: {},
			details_missing: ["Instrument", "Provisions"],
			can_edit: false,
		});
		const wrapper = mount(RuleVersionDetail, { props: { name: "rv-1", kind: "reference" }, global: globalMocks(), attachTo: document.body });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-rule-title"]').text()).toBe("Reservation rules");
		expect(wrapper.find('[data-testid="kt-procset-rule-details"]').text()).toBe("Details missing");
		expect(wrapper.find('[data-testid="kt-procset-rule-incomplete-notice"]').text()).toBe(
			"Complete the rule details and source checks before using this version. Missing: Instrument, Provisions."
		);
		expect(wrapper.find('[data-testid="kt-procset-rule-identifier"]').text()).toBe("RESERVATION-RULES");

		await wrapper.find('[data-testid="kt-procset-rule-rename"]').trigger("click");
		const dialog = wrapper.find('[data-testid="kt-procset-rule-rename-dialog"]');
		expect(dialog.find(".dialog-title").text()).toBe("Edit rule name");
		expect(document.activeElement?.getAttribute("data-testid")).toBe("kt-procset-rule-rename-input");
		api.renameRegulatoryReference.mockResolvedValue({ reference_set: "rs-res", display_name: "AGPO reservation" });
		await dialog.find('[data-testid="kt-procset-rule-rename-input"]').setValue("AGPO reservation");
		await dialog.find('[data-testid="kt-procset-rule-rename-save"]').trigger("click");
		await flushPromises();
		expect(api.renameRegulatoryReference).toHaveBeenCalledWith("rs-res", "AGPO reservation", "");
		expect(wrapper.find('[data-testid="kt-procset-rule-rename-dialog"]').exists()).toBe(false);
		expect(wrapper.emitted("renamed")).toHaveLength(1);
		// It stays on the detail and re-reads it; nothing navigates away.
		expect(wrapper.emitted("registered")).toBeFalsy();
		expect(api.getRegulatoryReferenceVersion).toHaveBeenCalledTimes(2);
		wrapper.unmount();
	});
});
