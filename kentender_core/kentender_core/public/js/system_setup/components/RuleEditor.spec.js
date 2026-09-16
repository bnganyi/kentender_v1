// CFG-CHG-002 v0.11 §10.6/§10.7 (C03-B/C) — one editor for all seven rule
// kinds, §7.3's recoverable two-command creation, and the new-version
// replacement statement.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({
	createRegulatoryReference: vi.fn(),
	saveRegulatoryReferenceVersion: vi.fn(),
}));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import RuleEditor from "./RuleEditor.vue";

const KINDS = [
	"Method eligibility",
	"Reservation rules",
	"Exclusive preference",
	"Preference margins",
	"Market price index",
	"Approval applicability",
	"Publication obligations",
];

function mountEditor(props = {}) {
	return mount(RuleEditor, {
		props: {
			kinds: KINDS,
			entityTypes: ["National Government Ministry", "County Government"],
			categories: ["Goods", "Works", "Services"],
			...props,
		},
		global: globalMocks(),
	});
}

describe("RuleEditor", () => {
	beforeEach(() => vi.clearAllMocks());

	it("offers exactly the seven kinds and swaps the kind-specific fields with the selection", async () => {
		const wrapper = mountEditor();
		expect(wrapper.findAll('[data-testid="kt-rule-kind"] option').map((o) => o.text())).toEqual(KINDS);

		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Reservation rules");
		expect(wrapper.find('[data-testid="kt-rr-code"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-po-id"]').exists()).toBe(false);

		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Publication obligations");
		expect(wrapper.find('[data-testid="kt-po-id"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-rr-code"]').exists()).toBe(false);
	});

	it("Method eligibility is delegated to its method profile rather than duplicated here", async () => {
		const wrapper = mountEditor();
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Method eligibility");
		expect(wrapper.find('[data-testid="kt-rule-delegated"]').text()).toContain("maintained as a method profile");
		expect(wrapper.find('[data-testid="kt-rule-save"]').attributes("disabled")).toBeDefined();
	});

	it("creating a rule runs §7.3's two commands in order and passes the kind's own payload", async () => {
		api.createRegulatoryReference.mockResolvedValue({ reference_set: "rs-1" });
		api.saveRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-1" });
		const wrapper = mountEditor();
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Reservation rules");
		await wrapper.find('[data-testid="kt-rule-name"]').setValue("Reservation rules");
		await wrapper.find('[data-testid="kt-rule-key"]').setValue("RESERVATION-RULES");
		await wrapper.find('[data-testid="kt-rule-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-rr-code"]').setValue("ANNUAL-TARGET");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();

		expect(api.createRegulatoryReference).toHaveBeenCalledWith({
			reference_key: "RESERVATION-RULES",
			reference_kind: "Reservation rules",
			display_name: "Reservation rules",
		});
		expect(api.saveRegulatoryReferenceVersion.mock.calls[0][0]).toMatchObject({
			reference_set: "rs-1",
			effective_from: "2027-07-01",
			payload: { obligation_code: "ANNUAL-TARGET" },
		});
		expect(wrapper.emitted("saved")).toBeTruthy();
	});

	it("§7.3 recovery: a failed version save keeps the entries and reuses the set instead of creating a second one", async () => {
		api.createRegulatoryReference.mockResolvedValue({ reference_set: "rs-1" });
		api.saveRegulatoryReferenceVersion.mockRejectedValueOnce(new Error("Enter the obligation code."));
		const wrapper = mountEditor();
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Reservation rules");
		await wrapper.find('[data-testid="kt-rule-name"]').setValue("Reservation rules");
		await wrapper.find('[data-testid="kt-rule-key"]').setValue("RESERVATION-RULES");
		await wrapper.find('[data-testid="kt-rule-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();

		expect(wrapper.find('[data-testid="kt-procset-rule-partial"]').text()).toContain(
			"Rule created; version not saved."
		);
		expect(wrapper.find('[data-testid="kt-rule-error"]').text()).toBe("Enter the obligation code.");
		// The entries survive for the retry.
		expect(wrapper.find('[data-testid="kt-rule-from"]').element.value).toBe("2027-07-01");

		api.saveRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-1" });
		await wrapper.find('[data-testid="kt-rr-code"]').setValue("ANNUAL-TARGET");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();

		expect(api.createRegulatoryReference).toHaveBeenCalledTimes(1);
		expect(api.saveRegulatoryReferenceVersion.mock.calls[1][0].reference_set).toBe("rs-1");
	});

	it("a new version states what it replaces and sends the predecessor, without a second set", async () => {
		api.saveRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-2" });
		const wrapper = mountEditor({
			referenceSet: "rs-1",
			currentVersion: {
				reference: "rv-1",
				reference_set: "rs-1",
				reference_kind: "Reservation rules",
				version_number: 1,
				effective_from: "2027-07-01",
				effective_until: "2028-06-30",
				verification_status: "Production verification pending",
				payload: { obligation_code: "ANNUAL-TARGET" },
			},
		});
		const replacement = wrapper.find('[data-testid="kt-rule-replacement"]');
		expect(replacement.text()).toContain("Earlier versions this replaces: Version 1.");
		expect(replacement.text()).toContain("Version 1 already needs source checks");
		expect(wrapper.find('[data-testid="kt-rule-kind"]').exists()).toBe(false);

		await wrapper.find('[data-testid="kt-rule-reason"]').setValue("Amended figures.");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();

		expect(api.createRegulatoryReference).not.toHaveBeenCalled();
		expect(api.saveRegulatoryReferenceVersion.mock.calls[0][0]).toMatchObject({
			reference_set: "rs-1",
			supersedes_version_ids: ["rv-1"],
			change_reason: "Amended figures.",
		});
	});
});
