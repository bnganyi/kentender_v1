// CFG-CHG-002 v0.11 §10.6/§10.7 (C03-B/C) — one editor for all seven rule
// kinds, §7.3's recoverable two-command creation, and the new-version
// replacement statement.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({
	createRegulatoryReference: vi.fn(),
	saveRegulatoryReferenceVersion: vi.fn(),
	updateRegulatoryReferenceVersion: vi.fn(),
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

	it("Method eligibility picks the method: an existing rule opens its new version, a new one opens the full method editor (D21)", async () => {
		const wrapper = mountEditor({
			methods: ["Open Tender", "Framework Agreement"],
			methodRules: [{ profile: "MPR-OPEN-TENDER-V1", procurement_method: "Open Tender" }],
		});
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Method eligibility");
		// No generic kind card or save for this kind: its own editor owns it.
		expect(wrapper.find('[data-testid="kt-rule-kind-fields"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-rule-save"]').exists()).toBe(false);

		await wrapper.find('[data-testid="kt-rule-method"]').setValue("Open Tender");
		expect(wrapper.find('[data-testid="kt-rule-method-exists"]').text()).toContain("Method eligibility — Open Tender already exists.");
		await wrapper.find('[data-testid="kt-rule-method-open"]').trigger("click");
		expect(wrapper.emitted("open-method-version")[0]).toEqual(["MPR-OPEN-TENDER-V1"]);

		await wrapper.find('[data-testid="kt-rule-method"]').setValue("Framework Agreement");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-procset-method-editor"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-mve-method"]').text()).toBe("Framework Agreement");
		expect(wrapper.find('[data-testid="kt-mve-save"]').text()).toBe("Save rule version");
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

	it("Reservation rules asks for the measure and fixes what it is measured against (CFG-CHG-002 v0.13 §10.7)", async () => {
		api.createRegulatoryReference.mockResolvedValue({ reference_set: "rs-1" });
		api.saveRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-1" });
		const wrapper = mountEditor();
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Reservation rules");
		const measure = wrapper.find('[data-testid="kt-rr-measure"]');
		expect(measure.findAll("option").map((o) => o.text())).toEqual(["Planned allocation", "Actual achievement"]);
		expect(measure.element.value).toBe("PlanningAllocation");
		// Measured against is a consequence of the measure, never a free choice,
		// and the retired budget-based options are gone.
		const against = wrapper.find('[data-testid="kt-rr-basis"]');
		expect(against.element.tagName).toBe("INPUT");
		expect(against.element.value).toBe("Eligible value of the current Annual Plan");
		expect(against.attributes("disabled")).toBeDefined();
		expect(wrapper.text()).not.toContain("Annual procurement budget");
		await measure.setValue("ImplementationAchievement");
		expect(wrapper.find('[data-testid="kt-rr-basis"]').element.value).toBe("Applicable actual procurement value");

		await wrapper.find('[data-testid="kt-rule-name"]').setValue("Reservation rules");
		await wrapper.find('[data-testid="kt-rule-key"]').setValue("RESERVATION-RULES");
		await wrapper.find('[data-testid="kt-rule-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-rr-code"]').setValue("AGPO-30");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();
		const sent = api.saveRegulatoryReferenceVersion.mock.calls[0][0].payload;
		expect(sent.measure_stage).toBe("ImplementationAchievement");
		expect(sent).not.toHaveProperty("denominator_basis");
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
		const replacement = wrapper.find('[data-testid="kt-rule-version-head"]');
		expect(replacement.text()).toContain("Earlier versions this replaces: Reservation rules Version 1.");
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

	it("corrects a reference rule in place, with no replacement claimed and no reason asked for", async () => {
		api.updateRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-1", version_number: 1 });
		const current = {
			reference: "rv-1",
			reference_set: "rs-reservation",
			reference_kind: "Reservation rules",
			version_number: 1,
			effective_from: "2094-07-01",
			effective_until: "2095-06-30",
			applicability_basis: "FiscalYearStart",
			applicability_entity_types: [],
			applicability_county: "All",
			applicability_categories: [],
			applicability_currency: "KES",
			source_instrument: "",
			provision: "",
			source_document: "",
			interpretation: "",
			payload: { obligation_code: "ANNUAL-TARGET", target_percent: 30 },
			expected_version: "2026-09-23 10:00:00",
		};
		const wrapper = mountEditor({ referenceSet: "rs-reservation", currentVersion: current, mode: "correct" });
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-rule-correcting-notice"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-rule-version-head"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="kt-rule-save"]').text()).toBe("Save changes");

		await wrapper.find('[data-testid="kt-rr-target"]').setValue("35");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();
		expect(api.saveRegulatoryReferenceVersion).not.toHaveBeenCalled();
		const call = api.updateRegulatoryReferenceVersion.mock.calls[0][0];
		expect(call.reference).toBe("rv-1");
		expect(call.expected_version).toBe("2026-09-23 10:00:00");
		expect(call.payload.target_percent).toBe(35);
		expect(wrapper.emitted("saved")).toHaveLength(1);
	});

	it("the board's kind fields reach the saved payload (C03BC #kinds)", async () => {
		api.createRegulatoryReference.mockResolvedValue({ reference_set: "rs-x" });
		api.saveRegulatoryReferenceVersion.mockResolvedValue({ reference: "rv-x" });
		const wrapper = mountEditor({ methods: ["Open Tender"] });
		await wrapper.find('[data-testid="kt-rule-name"]').setValue("Reservation");
		await wrapper.find('[data-testid="kt-rule-key"]').setValue("RES");
		await wrapper.find('[data-testid="kt-rule-from"]').setValue("2027-07-01");
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Reservation rules");
		const card = wrapper.find('[data-testid="kt-rule-kind-fields"]');
		expect(card.find(".card-kicker").text()).toBe("Reservation rules");
		expect(card.findAll("h6").map((h) => h.text())).toEqual(["Measure", "Annual target", "What the target is measured against", "Who qualifies", "How targets overlap"]);
		// A new rule's selects show their empty choice, not a blank.
		expect(wrapper.find('[data-testid="kt-rr-overlap"]').element.selectedOptions[0].text).toBe("Not yet established");
		await wrapper.find('[data-testid="kt-rr-code"]').setValue("AGPO");
		await wrapper.find('[data-testid="kt-rr-designation"]').setValue("Women");
		await wrapper.find('[data-testid="kt-rr-conditions"]').setValue("Registered AGPO certificate");
		await wrapper.find('[data-testid="kt-rr-sources"]').setValue("PPADA s.157(5)");
		// Related obligations only apply to a specified overlap.
		expect(wrapper.find('[data-testid="kt-rr-related"]').attributes("disabled")).toBeDefined();
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();
		expect(api.saveRegulatoryReferenceVersion.mock.calls[0][0].payload).toMatchObject({
			obligation_code: "AGPO",
			eligible_designations: ["Women"],
			applicability_conditions: "Registered AGPO certificate",
			source_references: "PPADA s.157(5)",
		});
	});

	it("preference margins, approval applicability and the price index keep the board's own controls", async () => {
		const wrapper = mountEditor({ methods: ["Open Tender"] });
		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Preference margins");
		await wrapper.find('[data-testid="kt-pm-lower-no"]').trigger("change");
		expect(wrapper.find('[data-testid="kt-pm-lower-no"]').element.checked).toBe(true);
		expect(wrapper.text()).toContain("Used during evaluation; this does not decide supplier entitlement in Planning.");

		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Approval applicability");
		await wrapper.find('[data-testid="kt-aa-entity"]').setValue("State Corporation");
		expect(wrapper.text()).toContain("Required entity evidence: Not yet established.");
		expect(wrapper.find('[data-testid="kt-aa-capacity"]').element.value).toBe("Configured statutory capacity");

		await wrapper.find('[data-testid="kt-rule-kind"]').setValue("Market price index");
		expect(wrapper.find('[data-testid="kt-mpi-rows"]').text()).toContain("Not published");
		await wrapper.find('[data-testid="kt-mpi-add"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-mpi-item-0"]').exists()).toBe(true);
		await wrapper.find('[data-testid="kt-mpi-remove-0"]').trigger("click");
		expect(wrapper.find('[data-testid="kt-mpi-item-0"]').exists()).toBe(false);
	});

	it("a stale or overlapping save shows the board's state with its way forward, and keeps the entries", async () => {
		const version = {
			reference: "rv-1",
			reference_set: "rs-1",
			reference_kind: "Reservation rules",
			version_number: 1,
			effective_from: "2027-07-01",
			effective_until: "2028-06-30",
			verification_status: "Production verification pending",
			payload: { obligation_code: "ANNUAL-TARGET" },
		};
		api.saveRegulatoryReferenceVersion.mockRejectedValueOnce(new Error("This record changed after you opened it. Refresh and review the latest version."));
		const wrapper = mountEditor({ referenceSet: "rs-1", currentVersion: version });
		await wrapper.find('[data-testid="kt-rule-reason"]').setValue("Amended figures.");
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-rule-stale"]').text()).toContain("Stale. This information has changed since you opened it.");
		await wrapper.find('[data-testid="kt-rule-review-latest"]').trigger("click");
		expect(wrapper.emitted("refresh")).toHaveLength(1);
		// The same version re-read keeps what was typed.
		await wrapper.setProps({ currentVersion: { ...version, expected_version: "later" } });
		expect(wrapper.find('[data-testid="kt-rule-reason"]').element.value).toBe("Amended figures.");
		expect(wrapper.find('[data-testid="kt-rule-stale"]').exists()).toBe(false);

		api.saveRegulatoryReferenceVersion.mockRejectedValueOnce(new Error("Select valid earlier versions and check the dates this replacement will cover."));
		await wrapper.find('[data-testid="kt-rule-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-rule-overlap"]').text()).toContain("Overlap. Rule versions overlap for the required date.");
		await wrapper.find('[data-testid="kt-rule-review-versions"]').trigger("click");
		expect(wrapper.emitted("review")).toHaveLength(1);
	});
});
