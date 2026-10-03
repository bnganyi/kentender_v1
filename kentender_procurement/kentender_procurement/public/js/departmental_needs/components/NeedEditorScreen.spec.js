// NDS-DES-14-QUANTITY-ERROR/CLOSED-EDITOR/PARTIAL-SUBMIT/SUBMIT-UNKNOWN and
// NDS-DES-15-MULTIPLE/SINGLE/PERSISTED — literal copy and control state this
// component renders, ported class-for-class from NDS Artboards.dc.html. The
// design-fidelity gate's landmark check cannot see plain notice text or a
// button's disabled state; both are pinned here instead.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import NeedEditorScreen from "./NeedEditorScreen.vue";

function baseProps(overrides = {}) {
	return {
		mode: "create",
		need: {},
		revision: {},
		context: { organisation_unit_label: "Digital Health", financial_year_label: "FY 2027/28" },
		departmentChoices: [],
		selectedDepartment: "",
		units: [{ name: "Each", unit_label: "Each" }],
		returnReason: null,
		history: [],
		errorSummary: "",
		fieldErrors: {},
		pending: false,
		submissionClosed: false,
		partialSubmit: null,
		submitUnknown: false,
		...overrides,
	};
}

const make = (overrides) => mount(NeedEditorScreen, { props: baseProps(overrides) });

describe("NeedEditorScreen — NDS-DES-14-QUANTITY-ERROR", () => {
	it("names a quantity of zero, not the unparseable-number message, and sends nothing", async () => {
		const w = make();
		await w.get('[data-testid="nds-required-by"]').setValue("2027-08-31");
		await w.get('[data-testid="nds-quantity"]').setValue("0");
		await w.get('[data-testid="nds-submit"]').trigger("click");
		expect(w.get('[data-testid="nds-quantity-error"]').text()).toBe("Enter a quantity greater than zero.");
		expect(w.emitted("submit")).toBeUndefined();
	});

	it("clears once a positive quantity is entered", async () => {
		const w = make();
		await w.get('[data-testid="nds-quantity"]').setValue("0");
		await w.get('[data-testid="nds-submit"]').trigger("click");
		expect(w.find('[data-testid="nds-quantity-error"]').exists()).toBe(true);
		await w.get('[data-testid="nds-quantity"]').setValue("5");
		await w.get('[data-testid="nds-submit"]').trigger("click");
		expect(w.find('[data-testid="nds-quantity-error"]').exists()).toBe(false);
	});
});

describe("NeedEditorScreen — NDS-DES-14-CLOSED-EDITOR", () => {
	it("names the closed state and disables Submit for a still-Draft continuation", () => {
		const w = make({ mode: "draft", need: { need_reference: "NDS-MOH-2027-0003" }, revision: { revision_status: "Draft", revision_number: 1 }, submissionClosed: true });
		expect(w.get('[data-testid="nds-submission-closed-note"]').text()).toBe(
			"New submissions are closed. You can save changes to this draft and submit if submissions reopen.",
		);
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeDefined();
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeUndefined();
		expect(w.get('[data-testid="nds-editor-cancel"]').attributes("disabled")).toBeUndefined();
	});

	it("never gates a Returned correction's resubmission — NDS-BR-002/003 exempts it", () => {
		// The artboard's own chosen example is a Returned correction, but
		// lifecycle.py's submit_need() only calls require_open_intake() when
		// prior === STATE_DRAFT, never for STATE_RETURNED — disabling Resubmit
		// here would incorrectly block a save the server actually accepts.
		const w = make({ mode: "correct", need: { need_reference: "NDS-MOH-2027-0003" }, revision: { revision_status: "Returned", revision_number: 2 }, submissionClosed: true });
		expect(w.find('[data-testid="nds-submission-closed-note"]').exists()).toBe(false);
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeUndefined();
	});
});

describe("NeedEditorScreen — NDS-DES-14-PARTIAL-SUBMIT", () => {
	it("names the saved-but-not-submitted fact with the real reference and revision, Submit disabled", () => {
		const w = make({
			partialSubmit: { need: "NDS-1", need_reference: "NDS-MOH-2027-0001", record_version: 1, revision_number: "1", intake_closed: true, reason: "Needs submission is not open." },
		});
		const notice = w.get('[data-testid="nds-partial-submit"]');
		expect(notice.text()).toContain("Your draft was saved, but it was not submitted.");
		expect(notice.text()).toContain("New submissions are closed. You can save changes to this draft and submit if submissions reopen.");
		expect(notice.text()).toContain("Reference");
		expect(notice.text()).toContain("NDS-MOH-2027-0001");
		expect(notice.text()).toContain("Revision");
		expect(notice.text()).toContain("1");
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeDefined();
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeUndefined();
	});
	it("any other refusal shows its actual reason and leaves Submit enabled for the corrected retry", () => {
		const w = make({
			partialSubmit: {
				need: "NDS-1",
				need_reference: "NDS-MOH-2027-0005",
				record_version: 1,
				revision_number: "1",
				intake_closed: false,
				reason: "Required-by date must fall within the target financial year.",
			},
		});
		const notice = w.get('[data-testid="nds-partial-submit"]');
		expect(notice.text()).toContain("Your draft was saved, but it was not submitted.");
		expect(notice.text()).not.toContain("New submissions are closed.");
		expect(w.get('[data-testid="nds-partial-submit-reason"]').text()).toBe(
			"Required-by date must fall within the target financial year.",
		);
		expect(notice.text()).toContain("NDS-MOH-2027-0005");
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeUndefined();
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeUndefined();
	});
	it("on the saved Draft's own route (§8.4), a closed-intake refusal disables Submit even before intake state reloads", () => {
		const w = make({
			mode: "draft",
			need: { need_reference: "NDS-MOH-2027-0001" },
			revision: { revision_status: "Draft", revision_number: 1 },
			submissionClosed: false,
			partialSubmit: { need: "NDS-1", need_reference: "NDS-MOH-2027-0001", record_version: 1, revision_number: "1", intake_closed: true, reason: "Needs submission is not open." },
		});
		expect(w.get('[data-testid="nds-partial-submit"]').text()).toContain("Your draft was saved, but it was not submitted.");
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeDefined();
	});
});

describe("NeedEditorScreen — NDS-DES-14-SUBMIT-UNKNOWN", () => {
	it("names the unconfirmed outcome and disables both writes, keeping Cancel", () => {
		const w = make({ submitUnknown: true });
		expect(w.get('[data-testid="nds-submit-unknown"]').text()).toBe(
			"We could not confirm whether submission succeeded. Checking the existing request…",
		);
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeDefined();
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeDefined();
		expect(w.get('[data-testid="nds-editor-cancel"]').attributes("disabled")).toBeUndefined();
	});
});

describe("NeedEditorScreen — NDS-DES-15-MULTIPLE", () => {
	it("offers the department choice and disables Save/Submit until one is picked", () => {
		const w = make({
			departmentChoices: [
				{ organisation_unit: "OU-1", organisation_unit_label: "Digital Health" },
				{ organisation_unit: "OU-2", organisation_unit_label: "Human Resources Management and Development" },
			],
			selectedDepartment: "",
		});
		expect(w.get('[data-testid="nds-department"]').exists()).toBe(true);
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeDefined();
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeDefined();
	});

	it("enables Save/Submit once a department is chosen", () => {
		const w = make({
			departmentChoices: [
				{ organisation_unit: "OU-1", organisation_unit_label: "Digital Health" },
				{ organisation_unit: "OU-2", organisation_unit_label: "Human Resources Management and Development" },
			],
			selectedDepartment: "OU-1",
		});
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeUndefined();
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeUndefined();
	});
});

describe("NeedEditorScreen — NDS-DES-15-SINGLE / PERSISTED", () => {
	it("SINGLE — one eligible department reads as fixed context, no selector", () => {
		const w = make({ departmentChoices: [] });
		expect(w.find('[data-testid="nds-department"]').exists()).toBe(false);
		expect(w.text()).toContain("Digital Health");
		expect(w.text()).toContain("FY 2027/28");
	});

	it("PERSISTED — an existing draft offers Withdraw need, Save changes, Submit for review, all enabled", () => {
		const w = make({
			mode: "draft",
			need: { need_reference: "NDS-MOH-2027-0004" },
			revision: { revision_status: "Draft", revision_number: 1 },
		});
		expect(w.get('[data-testid="nds-editor-cancel"]').text()).toBe("Withdraw need");
		expect(w.get('[data-testid="nds-save-draft"]').text()).toBe("Save changes");
		expect(w.get('[data-testid="nds-submit"]').text()).toBe("Submit for review");
		expect(w.get('[data-testid="nds-submit"]').attributes("disabled")).toBeUndefined();
	});

	it("PERSISTED — names Department and Financial year as labelled facts, matching the create-mode single-department reading above", () => {
		// Regression: this branch used to render "Digital Health · FY 2027/28"
		// as plain unlabelled spans (no `.kt-label` at all) — a genuine
		// structural gap the NDS-DES-15-PERSISTED fidelity test caught, since
		// its own artboard uses the same labelled kt-meta-row the create-mode
		// single-department branch already used.
		const w = make({
			mode: "draft",
			need: { need_reference: "NDS-MOH-2027-0004" },
			revision: { revision_status: "Draft", revision_number: 1 },
			context: { organisation_unit_label: "Digital Health", financial_year_label: "FY 2027/28" },
		});
		const labels = w.findAll(".kt-label").map((el) => el.text());
		expect(labels).toContain("Department");
		expect(labels).toContain("Financial year");
		expect(w.text()).toContain("Digital Health");
		expect(w.text()).toContain("FY 2027/28");
	});
});

// UAT issue #25 — Required by is limited to the target financial year.
describe("NeedEditorScreen — Required by stays inside the financial year", () => {
	const year = {
		organisation_unit_label: "Digital Health",
		financial_year_label: "FY 2027/28",
		financial_year_start: "2027-07-01",
		financial_year_end: "2028-06-30",
	};

	it("limits the date picker to the year's first and last day", () => {
		const input = make({ context: year }).get('[data-testid="nds-required-by"]');
		expect(input.attributes("min")).toBe("2027-07-01");
		expect(input.attributes("max")).toBe("2028-06-30");
	});

	it("tells the user the allowed dates and sends nothing for a date outside the year", async () => {
		for (const button of ["nds-save-draft", "nds-submit"]) {
			const w = make({ context: year });
			await w.get('[data-testid="nds-required-by"]').setValue("2030-01-31");
			await w.get(`[data-testid="${button}"]`).trigger("click");
			expect(w.get('[data-testid="nds-required-by-error"]').text()).toBe(
				"Required by must be between 1 Jul 2027 and 30 Jun 2028, the dates of FY 2027/28.",
			);
			expect(w.emitted("save")).toBeUndefined();
			expect(w.emitted("submit")).toBeUndefined();
		}
	});

	it("accepts the first and last day of the year and clears the message once corrected", async () => {
		const w = make({ context: year });
		const input = w.get('[data-testid="nds-required-by"]');
		await input.setValue("2030-01-31");
		await w.get('[data-testid="nds-save-draft"]').trigger("click");
		expect(w.find('[data-testid="nds-required-by-error"]').exists()).toBe(true);
		for (const day of ["2027-07-01", "2028-06-30"]) {
			await input.setValue(day);
			await w.get('[data-testid="nds-save-draft"]').trigger("click");
			expect(w.find('[data-testid="nds-required-by-error"]').exists()).toBe(false);
		}
		expect(w.emitted("save")).toHaveLength(2);
	});

	it("does not limit the date when the year's dates are not known", async () => {
		const w = make();
		expect(w.get('[data-testid="nds-required-by"]').attributes("min")).toBeUndefined();
		await w.get('[data-testid="nds-required-by"]').setValue("2030-01-31");
		await w.get('[data-testid="nds-save-draft"]').trigger("click");
		expect(w.emitted("save")).toHaveLength(1);
	});
});

// A failed unit load must not take the editor down (UAT #29).
describe("NeedEditorScreen — the Unit list could not be loaded", () => {
	it("says so beside the Unit field and offers Try again, leaving the form usable", async () => {
		const w = make({ units: [], unitsError: true });
		expect(w.get('[data-testid="nds-units-error"]').text()).toContain("The list of units could not be loaded.");
		expect(w.get('[data-testid="nds-title"]').attributes("disabled")).toBeUndefined();
		expect(w.get('[data-testid="nds-save-draft"]').attributes("disabled")).toBeUndefined();
		await w.get('[data-testid="nds-units-retry"]').trigger("click");
		expect(w.emitted("retry-units")).toHaveLength(1);
	});

	it("shows no message when the units loaded", () => {
		expect(make().find('[data-testid="nds-units-error"]').exists()).toBe(false);
	});
});
