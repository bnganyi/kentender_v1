// PLN-CHG-001 v1.23 §10.12 — TreasurySubmissionDialog component tests
// (U13-TREASURY-FORM / U13-CORRECT-EVIDENCE).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import TreasurySubmissionDialog from "./TreasurySubmissionDialog.vue";

function task(overrides = {}) {
	return {
		plan_title: "Ministry of Health Annual Procurement Plan 2027/28",
		plan_reference: "PLN-MOH-2027-001",
		version: { number: 1, reference: "PLN-MOH-2027-001-V1" },
		treasury_prior: null,
		treasury_evidence_id: "",
		...overrides,
	};
}

const PRIOR = {
	submitted_at: "2026-12-10 14:00:00",
	submitted_display: "10 Dec 2026, 14:00 EAT",
	channel: "Official correspondence",
	destination: "National Treasury",
	dispatch_reference: "MOH/APP/2027/001",
};

const make = (overrides) =>
	mount(TreasurySubmissionDialog, { props: { task: task(overrides), pending: false, error: "" } });

async function fill(w) {
	await w.find('[data-testid="pub-treasury-sent"]').setValue("2026-12-10T14:00");
	await w.find('[data-testid="pub-treasury-channel"]').setValue("Official correspondence");
	await w.find('[data-testid="pub-treasury-destination"]').setValue("National Treasury");
	await w.find('[data-testid="pub-treasury-dispatch"]').setValue("MOH/APP/2027/001");
}

describe("TreasurySubmissionDialog — U13-TREASURY-FORM", () => {
	it("names the plan it is recording a submission for", () => {
		const text = make().find('[data-testid="pub-treasury-plan"]').text();
		expect(text).toContain("PLN-MOH-2027-001");
		expect(text).toContain("1");
	});

	it("starts with the document confirmation unchecked and the action unavailable", async () => {
		const w = make();
		expect(w.find('[data-testid="pub-treasury-confirm"]').element.checked).toBe(false);
		await fill(w);
		expect(w.find('[data-testid="pub-treasury-submit"]').attributes("disabled")).toBeDefined();
		// Says what is missing rather than leaving a dead button.
		expect(w.find('[data-testid="pub-treasury-hint"]').text()).toBe(
			"Confirm the document match to record this submission.",
		);
	});

	it("records once the fields and the confirmation are both there", async () => {
		const w = make();
		await fill(w);
		await w.find('[data-testid="pub-treasury-confirm"]').setValue(true);
		expect(w.find('[data-testid="pub-treasury-submit"]').text()).toBe("Record submission");
		expect(w.find('[data-testid="pub-treasury-submit"]').attributes("disabled")).toBeUndefined();

		await w.find('[data-testid="pub-treasury-submit"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.dispatch_reference).toBe("MOH/APP/2027/001");
		expect(payload.exact_document_confirmed).toBe(true);
	});

	it("asks for the fields before the confirmation means anything", () => {
		expect(make().find('[data-testid="pub-treasury-hint"]').text()).toBe(
			"Enter the date sent, channel, destination and dispatch reference.",
		);
	});
});

describe("TreasurySubmissionDialog — U13-CORRECT-EVIDENCE", () => {
	it("keeps the recorded evidence visible above the new values", () => {
		const w = make({ treasury_prior: PRIOR, treasury_evidence_id: "TSE-0001" });
		expect(w.find('[data-testid="pub-treasury-title"]').text()).toBe("Correct submission details");
		const prior = w.find('[data-testid="pub-treasury-prior"]').text();
		expect(prior).toContain("10 Dec 2026, 14:00 EAT");
		expect(prior).toContain("Official correspondence");
		expect(prior).toContain("MOH/APP/2027/001");
		// No overwrite language anywhere.
		expect(w.text()).not.toContain("overwrite");
		expect(w.text()).not.toContain("replace");
	});

	it("requires a reason, and asks for the document match only once", async () => {
		const w = make({ treasury_prior: PRIOR, treasury_evidence_id: "TSE-0001" });
		// The confirmation belongs to the original record, not to correcting it.
		expect(w.find('[data-testid="pub-treasury-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="pub-treasury-submit"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pub-treasury-hint"]').text()).toBe(
			"State why the recorded details are being corrected.",
		);

		await w.find('[data-testid="pub-treasury-reason"]').setValue("The dispatch reference was transcribed incorrectly.");
		expect(w.find('[data-testid="pub-treasury-submit"]').text()).toBe("Save corrected details");
		expect(w.find('[data-testid="pub-treasury-submit"]').attributes("disabled")).toBeUndefined();
	});

	it("prefills the recorded values so only what changed has to be retyped", () => {
		const w = make({ treasury_prior: PRIOR, treasury_evidence_id: "TSE-0001" });
		expect(w.find('[data-testid="pub-treasury-channel"]').element.value).toBe("Official correspondence");
		expect(w.find('[data-testid="pub-treasury-dispatch"]').element.value).toBe("MOH/APP/2027/001");
	});
});
