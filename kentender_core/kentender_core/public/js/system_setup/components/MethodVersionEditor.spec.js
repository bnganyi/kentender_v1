// CFG-CHG-002 v0.11 §4.6 / §10.6 — the Method eligibility editor. An
// administrator may change anything about a method rule. What that produces
// depends on whether the rule could already matter to anyone: a Version
// nothing has pinned and that has not taken effect is corrected in place, and
// any other is replaced by a new immutable Version that supersedes it. The
// server decides which; this screen is told.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ getMethodProfile: vi.fn(), registerMethodProfileVersion: vi.fn(), updateMethodProfile: vi.fn() }));
vi.mock("../data/procurementSettingsApi.js", () => ({ procurementSettingsApi: api }));

import MethodVersionEditor from "./MethodVersionEditor.vue";

const profile = {
	profile: "MPR-OPEN-TENDER-V1",
	procurement_method: "Open Tender",
	version_number: 1,
	status: "Active",
	effective_from: "2027-05-01",
	effective_until: "2028-06-30",
	applicability_basis: "Planned invitation date",
	verification_status: "Production verification pending",
	source_instrument: "Public Procurement and Asset Disposal Regulations",
	provision: "Second Schedule; s.96",
	source_document: "",
	change_reason: "",
	supersedes_version_ids: [],
	can_edit: false,
	edit_blocked_reason: "This rule has already taken effect, so it cannot change. Create a new version instead.",
	expected_version: "2026-09-23 10:00:00",
	conditions: [
		{
			condition_id: "G-VALUE",
			kind: "Known fact",
			description: "No fixed maximum for goods.",
			procurement_category: "Goods",
			minimum_amount: 0,
			maximum_amount: 0,
			cumulative_basis: "Funds allocated",
			mandatory: true,
			required_evidence: "Method eligibility record",
			authorisation_actor: "",
			authorisation_stage: "",
			statutory_reference: "Second Schedule; s.96",
		},
		{
			condition_id: "W-VALUE",
			kind: "Known fact",
			description: "No fixed maximum for works.",
			procurement_category: "Works",
			minimum_amount: 0,
			maximum_amount: 0,
			cumulative_basis: "Funds allocated",
			mandatory: true,
			required_evidence: "Method eligibility record",
			authorisation_actor: "",
			authorisation_stage: "",
			statutory_reference: "Second Schedule; s.96",
		},
	],
};

const VOCAB = {
	categories: ["Goods", "Works", "Services"],
	conditionKinds: ["Known fact", "Declaration"],
	cumulativeBases: ["None", "Per request", "Per item per financial year", "Per procurement", "Funds allocated", "Section conditions"],
	applicabilityBases: ["Planned invitation date", "Financial year start"],
	verificationStatuses: ["Production verification pending", "Verified"],
};

function mountEditor(props = {}) {
	return mount(MethodVersionEditor, {
		props: { name: "MPR-OPEN-TENDER-V1", ...VOCAB, ...props },
		global: globalMocks(),
	});
}

async function openEditor(props) {
	const wrapper = mountEditor(props);
	await flushPromises();
	return wrapper;
}

// The editor is only usable once the reason is given; every test that
// reaches the save button goes through this.
async function giveReason(wrapper, text = "Goods maximum raised by the 2028 threshold review.") {
	await wrapper.find('[data-testid="kt-mve-reason"]').setValue(text);
}

describe("MethodVersionEditor", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		api.getMethodProfile.mockResolvedValue(profile);
		api.registerMethodProfileVersion.mockResolvedValue({ profile: "MPR-OPEN-TENDER-V2", version_number: 2, superseded: ["MPR-OPEN-TENDER-V1"] });
		api.updateMethodProfile.mockResolvedValue({ profile: "MPR-OPEN-TENDER-V1", version_number: 1, superseded: [] });
	});

	it("opens on the current Version's own values, every condition fully editable", async () => {
		const wrapper = await openEditor();
		expect(wrapper.find('[data-testid="kt-mve-title"]').text()).toBe("Method eligibility — new version");
		expect(wrapper.find('[data-testid="kt-mve-method"]').text()).toBe("Open Tender");
		expect(wrapper.find('[data-testid="kt-mve-from"]').element.value).toBe("2027-05-01");
		expect(wrapper.find('[data-testid="kt-mve-until"]').element.value).toBe("2028-06-30");
		expect(wrapper.find('[data-testid="kt-mve-basis"]').element.value).toBe("Planned invitation date");
		expect(wrapper.findAll('[data-testid^="kt-mve-condition-"]')).toHaveLength(2);
		expect(wrapper.find('[data-testid="kt-mve-id-0"]').element.value).toBe("G-VALUE");
		expect(wrapper.find('[data-testid="kt-mve-description-0"]').element.value).toBe("No fixed maximum for goods.");
		expect(wrapper.find('[data-testid="kt-mve-basis-0"]').element.value).toBe("Funds allocated");
		expect(wrapper.find('[data-testid="kt-mve-evidence-0"]').element.value).toBe("Method eligibility record");
		// The thin dialog this replaces could not touch these at all.
		expect(wrapper.find('[data-testid="kt-mve-category-0"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-mve-kind-0"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-mve-min-0"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="kt-mve-actor-0"]').exists()).toBe(true);
	});

	it("offers only the server's own vocabularies", async () => {
		const wrapper = await openEditor();
		const options = (testid) => wrapper.find(`[data-testid="${testid}"]`).findAll("option").map((o) => o.element.value);
		expect(options("kt-mve-kind-0")).toEqual(["Known fact", "Declaration"]);
		expect(options("kt-mve-basis-0")).toEqual(VOCAB.cumulativeBases);
		expect(options("kt-mve-category-0")).toEqual(["", "Goods", "Works", "Services"]);
		expect(options("kt-mve-basis")).toEqual(["", "Planned invitation date", "Financial year start"]);
	});

	it("keeps a stored applicability basis this release does not list, rather than silently dropping it", async () => {
		api.getMethodProfile.mockResolvedValue({ ...profile, applicability_basis: "Some earlier basis" });
		const wrapper = await openEditor();
		expect(wrapper.find('[data-testid="kt-mve-basis"]').element.value).toBe("Some earlier basis");
		await giveReason(wrapper);
		await wrapper.find('[data-testid="kt-mve-save"]').trigger("click");
		await flushPromises();
		expect(api.registerMethodProfileVersion.mock.calls[0][0].applicability_basis).toBe("Some earlier basis");
	});

	it("adds and removes conditions, and saves the edited set as a new Version that replaces the one opened", async () => {
		const wrapper = await openEditor();
		await wrapper.find('[data-testid="kt-mve-remove-1"]').trigger("click");
		expect(wrapper.findAll('[data-testid^="kt-mve-condition-"]')).toHaveLength(1);

		await wrapper.find('[data-testid="kt-mve-add"]').trigger("click");
		await wrapper.find('[data-testid="kt-mve-id-1"]').setValue("S-DECLARE");
		await wrapper.find('[data-testid="kt-mve-kind-1"]').setValue("Declaration");
		await wrapper.find('[data-testid="kt-mve-category-1"]').setValue("Services");
		await wrapper.find('[data-testid="kt-mve-description-1"]').setValue("The planner declares the service is unique.");
		await wrapper.find('[data-testid="kt-mve-max-1"]').setValue("5000000");
		await wrapper.find('[data-testid="kt-mve-basis-1"]').setValue("Per request");
		await wrapper.find('[data-testid="kt-mve-evidence-1"]').setValue("Signed declaration");
		await wrapper.find('[data-testid="kt-mve-actor-1"]').setValue("Accounting Officer");
		await wrapper.find('[data-testid="kt-mve-stage-1"]').setValue("Before invitation");
		await wrapper.find('[data-testid="kt-mve-from"]').setValue("2028-07-01");
		await giveReason(wrapper);

		await wrapper.find('[data-testid="kt-mve-save"]').trigger("click");
		await flushPromises();

		const call = api.registerMethodProfileVersion.mock.calls[0][0];
		expect(call.procurement_method).toBe("Open Tender");
		expect(call.effective_from).toBe("2028-07-01");
		expect(call.replaces).toBe("MPR-OPEN-TENDER-V1");
		expect(call.change_reason).toBe("Goods maximum raised by the 2028 threshold review.");
		expect(call.conditions.map((row) => row.condition_id)).toEqual(["G-VALUE", "S-DECLARE"]);
		expect(call.conditions[1]).toMatchObject({
			kind: "Declaration",
			procurement_category: "Services",
			maximum_amount: 5000000,
			cumulative_basis: "Per request",
			required_evidence: "Signed declaration",
			authorisation_actor: "Accounting Officer",
			authorisation_stage: "Before invitation",
		});
		// The parent is told which Version now exists so it can show it.
		expect(wrapper.emitted("saved")[0]).toEqual(["MPR-OPEN-TENDER-V2"]);
	});

	it("says what is missing instead of letting the server refuse the save", async () => {
		const wrapper = await openEditor();
		const blocked = () => wrapper.find('[data-testid="kt-mve-blocked"]').text();
		const saveDisabled = () => wrapper.find('[data-testid="kt-mve-save"]').attributes("disabled") !== undefined;

		expect(blocked()).toContain("Say why this version replaces the earlier one");
		expect(saveDisabled()).toBe(true);

		await wrapper.find('[data-testid="kt-mve-id-1"]').setValue("G-VALUE");
		expect(blocked()).toContain("G-VALUE is used twice");

		await wrapper.find('[data-testid="kt-mve-id-1"]').setValue("");
		expect(blocked()).toContain("Give every condition an identifier");

		await wrapper.find('[data-testid="kt-mve-remove-1"]').trigger("click");
		await wrapper.find('[data-testid="kt-mve-remove-0"]').trigger("click");
		expect(blocked()).toContain("Add at least one condition");

		await wrapper.find('[data-testid="kt-mve-from"]').setValue("");
		expect(blocked()).toContain("Enter the date this version applies from");
		expect(api.registerMethodProfileVersion).not.toHaveBeenCalled();
	});

	it("reports a server refusal inline and keeps the form, so the entries are not lost", async () => {
		api.registerMethodProfileVersion.mockRejectedValue(new Error("Condition G-VALUE: unknown category."));
		const wrapper = await openEditor();
		await giveReason(wrapper);
		await wrapper.find('[data-testid="kt-mve-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="kt-mve-error"]').text()).toContain("unknown category");
		expect(wrapper.emitted("saved")).toBeFalsy();
		expect(wrapper.find('[data-testid="kt-mve-id-0"]').element.value).toBe("G-VALUE");
		expect(wrapper.find('[data-testid="kt-mve-reason"]').element.value).toContain("threshold review");
	});

	it("states the replacement and its effect before the save, never after", async () => {
		const wrapper = await openEditor();
		const replacement = wrapper.find('[data-testid="kt-mve-replacement"]');
		expect(replacement.text()).toContain("Earlier versions this replaces: Method eligibility Version 1.");
		expect(replacement.text()).toContain("Version 1 already needs source checks");
		expect(replacement.text()).toContain("The replacement will not be usable for affected new decisions");
	});

	// Owner decision 23 Sep 2026 — a rule nothing uses and that has not taken
	// effect is corrected in place; only a frozen one costs a new Version.
	describe("correcting a rule in place", () => {
		it("changes this Version rather than replacing it, and asks for no reason", async () => {
			const wrapper = await openEditor({ mode: "correct" });
			expect(wrapper.find('[data-testid="kt-mve-title"]').text()).toBe("Method eligibility — edit rule");
			expect(wrapper.find('[data-testid="kt-mve-correcting-notice"]').text()).toContain("Once either happens, changing it means a new version");
			// Nothing is being replaced, so nothing claims to be.
			expect(wrapper.find('[data-testid="kt-mve-replacement"]').exists()).toBe(false);
			expect(wrapper.find('[data-testid="kt-mve-reason"]').exists()).toBe(false);
			expect(wrapper.find('[data-testid="kt-mve-save"]').text()).toBe("Save changes");
			// A reason is not required here, so the form is usable as opened.
			expect(wrapper.find('[data-testid="kt-mve-save"]').attributes("disabled")).toBeUndefined();

			await wrapper.find('[data-testid="kt-mve-max-0"]').setValue("900000");
			await wrapper.find('[data-testid="kt-mve-save"]').trigger("click");
			await flushPromises();

			expect(api.registerMethodProfileVersion).not.toHaveBeenCalled();
			const call = api.updateMethodProfile.mock.calls[0][0];
			expect(call.profile).toBe("MPR-OPEN-TENDER-V1");
			expect(call.expected_version).toBe("2026-09-23 10:00:00");
			expect(call.conditions[0].maximum_amount).toBe(900000);
			expect(call.change_reason).toBeUndefined();
			expect(call.replaces).toBeUndefined();
			expect(wrapper.emitted("saved")[0]).toEqual(["MPR-OPEN-TENDER-V1"]);
		});

		it("still holds the rule to the same standard as a new version", async () => {
			const wrapper = await openEditor({ mode: "correct" });
			await wrapper.find('[data-testid="kt-mve-remove-1"]').trigger("click");
			await wrapper.find('[data-testid="kt-mve-remove-0"]').trigger("click");
			expect(wrapper.find('[data-testid="kt-mve-blocked"]').text()).toContain("Add at least one condition");
			expect(wrapper.find('[data-testid="kt-mve-save"]').attributes("disabled")).toBeDefined();
		});

		it("reports the server's refusal when the rule froze while it was open", async () => {
			api.updateMethodProfile.mockRejectedValue(new Error("A plan already uses this rule, so it cannot change. Create a new version instead."));
			const wrapper = await openEditor({ mode: "correct" });
			await wrapper.find('[data-testid="kt-mve-save"]').trigger("click");
			await flushPromises();
			expect(wrapper.find('[data-testid="kt-mve-error"]').text()).toContain("Create a new version instead");
			expect(wrapper.emitted("saved")).toBeFalsy();
		});
	});

	it("shows the not-available state for a rule it cannot read", async () => {
		api.getMethodProfile.mockRejectedValue(new Error("That method profile version does not exist."));
		const wrapper = await openEditor({ name: "MPR-NOPE-V9" });
		expect(wrapper.find('[data-testid="kt-mve-load-error"]').text()).toContain("This rule isn't available to you");
		expect(wrapper.find('[data-testid="kt-mve-save"]').exists()).toBe(false);
	});
});
