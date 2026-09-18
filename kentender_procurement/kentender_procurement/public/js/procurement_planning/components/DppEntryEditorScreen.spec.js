// PLN-CHG-001 v1.23 §10.4 — DppEntryEditorScreen component tests
// (U04-DIRECT / U04-EDIT).
//
// A requirement the department states itself. Everything on the page is the
// department's own; nothing here belongs to Planning, procurement or Strategy.
// Funding for an accepted requirement is not on this page at all — it opens
// beneath its own row on the plan (U03-FUNDING).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DppEntryEditorScreen from "./DppEntryEditorScreen.vue";

const UNITS = [
	{ id: "Programme", label: "Programme" },
	{ id: "Each", label: "Each" },
];

const LINES = [
	{ id: "BL-1", reference: "MOH-BL-DHI-2027", title: "Digital health infrastructure programme", label: "MOH-BL-DHI-2027 — Digital health infrastructure programme" },
];

function editor(overrides = {}) {
	return {
		outcome: "OK",
		dpp_reference: "DPP-MOH-DH-2027-001",
		dpp_version: "DPPV-MOH-DH-2027-001-V1",
		record_version: 2,
		mutable: true,
		can_edit: true,
		currency: "KES",
		context: { department: "Digital Health", financial_year: "FY 2027/28" },
		budget_lines: LINES,
		units: UNITS,
		...overrides,
	};
}

const SAVED = {
	entry_id: "DPPE-MOH-DH-2027-004",
	title: "Digital health platform security assessment",
	description: "Assess the security of the national digital health platform and provide a prioritised remediation report",
	expected_operational_result: "The Ministry receives a prioritised and actionable security remediation plan",
	quantity: 1,
	unit: "Programme",
	required_by_date: "2027-10-31",
	budget_line: "BL-1",
	indicative_amount: 20000000,
};

const make = (overrides) =>
	mount(DppEntryEditorScreen, { props: { editor: editor(overrides), pending: false, errorSummary: "" } });

describe("DppEntryEditorScreen — U04-DIRECT", () => {
	it("says what this page is for and names the department and year", () => {
		const w = make();
		expect(w.find('[data-testid="dpp-editor-title"]').text()).toBe("Add a requirement");
		expect(w.text()).toContain("Add a departmental requirement that was not created through Departmental Needs.");
		const context = w.find('[data-testid="dpp-editor-context"]').text();
		expect(context).toContain("Digital Health");
		expect(context).toContain("FY 2027/28");
	});

	it("offers exactly the eight departmental facts and nothing else", () => {
		const w = make();
		for (const id of ["title", "description", "result", "quantity", "unit", "required-by", "budget-line", "amount"]) {
			expect(w.find(`[data-testid="dpp-f-${id}"]`).exists()).toBe(true);
		}
		// Exactly eight controls: none of the Need, bypass, Strategy, method,
		// classification or attachment fields the page must not carry.
		expect(w.findAll("input, textarea, select")).toHaveLength(8);
		const text = w.text();
		for (const absent of ["bypass", "Strategic objective", "Procurement method", "Attachment", "Classification"]) {
			expect(text).not.toContain(absent);
		}
	});

	it("will not add an incomplete requirement", async () => {
		const w = make();
		expect(w.find('[data-testid="dpp-editor-save"]').attributes("disabled")).toBeDefined();

		await w.find('[data-testid="dpp-f-title"]').setValue(SAVED.title);
		await w.find('[data-testid="dpp-f-description"]').setValue(SAVED.description);
		await w.find('[data-testid="dpp-f-result"]').setValue(SAVED.expected_operational_result);
		await w.find('[data-testid="dpp-f-quantity"]').setValue("1");
		await w.find('[data-testid="dpp-f-unit"]').setValue("Programme");
		await w.find('[data-testid="dpp-f-required-by"]').setValue("2027-10-31");
		// Still short of a budget line and a cost.
		expect(w.find('[data-testid="dpp-editor-save"]').attributes("disabled")).toBeDefined();

		await w.find('[data-testid="dpp-f-budget-line"]').setValue("BL-1");
		await w.find('[data-testid="dpp-f-amount"]').setValue("20000000");
		expect(w.find('[data-testid="dpp-editor-save"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="dpp-f-budget-line-code"]').text()).toBe("MOH-BL-DHI-2027");

		await w.find('[data-testid="dpp-editor-save"]').trigger("click");
		expect(w.emitted("save-direct")[0][0]).toEqual({
			title: SAVED.title,
			description: SAVED.description,
			expected_operational_result: SAVED.expected_operational_result,
			// A number field yields a number, not the string the user typed.
			quantity: 1,
			unit: "Programme",
			required_by_date: "2027-10-31",
			budget_line: "BL-1",
			indicative_amount: 20000000,
		});
	});

	it("offers no removal for a requirement that does not exist yet", () => {
		expect(make().find('[data-testid="dpp-editor-remove"]').exists()).toBe(false);
		expect(make().find('[data-testid="dpp-editor-cancel"]').text()).toBe("Cancel");
	});
});

describe("DppEntryEditorScreen — U04-EDIT", () => {
	it("leads with the requirement's own name and reference", () => {
		const w = make({ entry: SAVED });
		expect(w.find('[data-testid="dpp-editor-title"]').text()).toBe(SAVED.title);
		expect(w.find('[data-testid="dpp-editor-reference"]').text()).toBe("DPPE-MOH-DH-2027-004");
	});

	it("loads the saved values into the controls", () => {
		const w = make({ entry: SAVED });
		expect(w.find('[data-testid="dpp-f-title"]').element.value).toBe(SAVED.title);
		expect(w.find('[data-testid="dpp-f-quantity"]').element.value).toBe("1");
		expect(w.find('[data-testid="dpp-f-unit"]').element.value).toBe("Programme");
		expect(w.find('[data-testid="dpp-f-amount"]').element.value).toBe("20000000");
	});

	it("offers removal, a way back, and a save that names what it saves", async () => {
		const w = make({ entry: SAVED });
		expect(w.find('[data-testid="dpp-editor-remove"]').text()).toBe("Remove requirement");
		expect(w.find('[data-testid="dpp-editor-cancel"]').text()).toBe("Back to departmental plan");
		expect(w.find('[data-testid="dpp-editor-save"]').text()).toBe("Save requirement");

		await w.find('[data-testid="dpp-editor-remove"]').trigger("click");
		expect(w.emitted("remove")).toHaveLength(1);
	});

	it("does not discard typing on a refresh that carries nothing new", async () => {
		const w = make({ entry: SAVED });
		await w.find('[data-testid="dpp-f-title"]').setValue("A title the department is still typing");
		// Same record_version: nothing changed on the server.
		await w.setProps({ editor: editor({ entry: SAVED }) });
		expect(w.find('[data-testid="dpp-f-title"]').element.value).toBe("A title the department is still typing");
	});
});

describe("DppEntryEditorScreen — a submitted plan", () => {
	it("keeps every value and offers no way to change it", () => {
		const w = make({ entry: SAVED, mutable: false });
		expect(w.find('[data-testid="dpp-f-title"]').element.value).toBe(SAVED.title);
		expect(w.find('[data-testid="dpp-f-title"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="dpp-editor-save"]').exists()).toBe(false);
		expect(w.find('[data-testid="dpp-editor-remove"]').exists()).toBe(false);
	});
});

describe("DppEntryEditorScreen — a refusal", () => {
	it("says why and keeps what was typed", async () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: editor({ entry: SAVED }), pending: false, errorSummary: "That budget line is not eligible for this department." },
		});
		expect(w.find('[data-testid="dpp-editor-error"]').text()).toBe(
			"That budget line is not eligible for this department.",
		);
		expect(w.find('[data-testid="dpp-f-title"]').element.value).toBe(SAVED.title);
	});
});
