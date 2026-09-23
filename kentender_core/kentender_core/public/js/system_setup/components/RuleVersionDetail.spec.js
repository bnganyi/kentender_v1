// C03-detail — a referenced rule Version, read-only, with Create new version.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ getMethodProfile: vi.fn(), getRegulatoryReferenceVersion: vi.fn(), registerMethodProfileVersion: vi.fn() }));
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

	it("renders the C03-detail facts in order, the pending status and Not attached", async () => {
		const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-rule-title"]').text()).toBe("Method eligibility — Open Tender — Version 1");
		const labels = wrapper.findAll('[data-testid="kt-procset-rule-card"] .kt-label').map((l) => l.text());
		// §10.6's saved detail: the summary facts, then the four supporting
		// groups (rule details, applicability, sources, usage).
		expect(labels).toEqual([
			"Rule kind",
			"Version",
			"Which date determines the rule to use?",
			"Applies from",
			"Applies until",
			"Source check",
			"Details",
			"Method",
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
		]);
		expect(wrapper.text()).toContain("1 Jul 2027");
		expect(wrapper.text()).toContain("Not attached");
		expect(wrapper.find('[data-testid="kt-procset-rule-verification"]').text()).toBe("Source check needed");
		expect(wrapper.find('[data-testid="kt-procset-rule-incomplete"]').text()).toBe("Required conditions not yet completed");
		expect(wrapper.find('[data-testid="kt-procset-rule-values"]').text()).toContain("No fixed maximum for goods.");
		expect(wrapper.findAll("input").length).toBe(0);
	});

	it("offers Edit rule only while the server says the rule can still be corrected", async () => {
		// Frozen: the fixture carries can_edit false, so the only way to change
		// the rule is a new version.
		const frozen = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
		expect(frozen.find('[data-testid="kt-procset-rule-edit"]').exists()).toBe(false);
		expect(frozen.find('[data-testid="kt-procset-rule-new-version"]').exists()).toBe(true);

		api.getMethodProfile.mockResolvedValue({ ...profile, can_edit: true, edit_blocked_reason: "" });
		const editable = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: [] }, global: globalMocks() });
		await flushPromises();
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
});
