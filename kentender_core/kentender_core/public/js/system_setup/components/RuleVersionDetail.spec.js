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

	it("Create new version opens the dialog seeded from the current Version; a masked record shows the not-available state", async () => {
		const wrapper = mount(RuleVersionDetail, { props: { name: "MPR-OPEN-TENDER-V1", kind: "method", verificationStatuses: ["Production verification pending", "Verified"] }, global: globalMocks() });
		await flushPromises();
		await wrapper.find('[data-testid="kt-procset-rule-new-version"]').trigger("click");
		const dialog = wrapper.find('[data-testid="kt-procset-new-version"]');
		expect(dialog.exists()).toBe(true);
		expect(dialog.find('[data-testid="kt-nv-effective-from"]').element.value).toBe("2027-07-01");
		expect(dialog.find('[data-testid="kt-nv-conditions"]').text()).toContain("G-VALUE");

		api.getMethodProfile.mockRejectedValueOnce(new Error("That method profile version does not exist."));
		const masked = mount(RuleVersionDetail, { props: { name: "MPR-NOPE-V9", kind: "method" }, global: globalMocks() });
		await flushPromises();
		expect(masked.find('[data-testid="kt-procset-rule-error"]').text()).toContain("This record isn't available to you");
	});
});
