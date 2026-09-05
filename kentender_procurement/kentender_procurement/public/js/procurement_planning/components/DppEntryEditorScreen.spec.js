// PLN-CHG-001 v1.12 §15 — DppEntryEditorScreen component tests (D14):
// PLN-DES-03 (Need funding, six read-only facts, funding only) and
// PLN-DES-04 (direct requirement, exactly the eight values).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DppEntryEditorScreen from "./DppEntryEditorScreen.vue";

const CONTEXT = {
	department: "OU-MOH-DHI — Digital Health",
	financial_year: "FY 2027/28",
};

const BUDGET_LINES = [
	{
		id: "MOH-BL-DHI-2027",
		label: "MOH-BL-DHI-2027 — Digital health infrastructure programme",
		approved_display: "KES 100,000,000",
		currency: "KES",
	},
];

const NEED_EDITOR = {
	outcome: "OK",
	dpp_reference: "DPP-MOH-DHI-2027-001",
	record_version: 3,
	dpp_version: "V1",
	mutable: true,
	context: CONTEXT,
	budget_lines: BUDGET_LINES,
	currency: "KES",
	units: [{ id: "UNIT-PROGRAMME", label: "Programme" }],
	entry: {
		entry_id: "E1",
		source_origin: "Accepted Departmental Need",
		title: "National digital health infrastructure upgrade",
		description:
			"Procure and implement national digital health infrastructure across priority health facilities.",
		expected_operational_result:
			"Priority health facilities can use secure and interoperable digital health services.",
		quantity: 1,
		quantity_display: "1 programme",
		unit: "UNIT-PROGRAMME",
		unit_label: "Programme",
		required_by_date: "2027-08-31",
		required_by_display: "31 Aug 2027",
		budget_line: "",
		indicative_amount: null,
		need_reference_line: "NDS-MOH-2027-0001 · Version 1",
	},
};

const DIRECT_EDITOR = {
	...NEED_EDITOR,
	entry: undefined,
	units: [{ id: "UNIT-SERVICE", label: "Service" }],
};

describe("DppEntryEditorScreen — PLN-DES-03 (Need funding)", () => {
	it("renders the six Need facts read-only plus the accepted reference", () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: NEED_EDITOR, pending: false, errorSummary: "" },
		});
		expect(w.find(".kt-page-title").text()).toBe("Complete funding details");
		expect(w.find(".kt-page-lede").text()).toContain(
			"Add the Planning-owned funding details for this accepted departmental requirement."
		);
		const facts = w.find('[data-testid="dpp-need-facts"]');
		expect(facts.text()).toContain("National digital health infrastructure upgrade");
		expect(facts.text()).toContain("Priority health facilities can use secure");
		expect(facts.text()).toContain("1 programme");
		expect(facts.text()).toContain("NDS-MOH-2027-0001 · Version 1");
		// PLN-DES-03 order: Title, Description, Expected operational result,
		// Quantity, Unit, Required by, Accepted Need
		expect(facts.findAll("label").map((l) => l.text())).toEqual([
			"Title", "Description", "Expected operational result", "Quantity", "Unit", "Required by", "Accepted Need",
		]);
		expect(facts.text()).toContain("Programme");
		// no editable control renders a Need fact (§12.3)
		expect(facts.findAll("input, textarea, select")).toHaveLength(0);
	});

	it("offers only Budget Line + amount and emits save-funding with exactly those", async () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: NEED_EDITOR, pending: false, errorSummary: "" },
		});
		const funding = w.find('[data-testid="dpp-funding"]');
		expect(funding.find(".kt-card-title").text()).toBe("Planning funding");
		expect(funding.find('label[for="dpp-budget-line"]').text()).toBe("Procurement Budget Line");
		expect(funding.text()).toContain("KES");
		await w.find('[data-testid="dpp-f-budget-line"]').setValue("MOH-BL-DHI-2027");
		await w.find('[data-testid="dpp-f-amount"]').setValue("80000000");
		await w.find('[data-testid="dpp-editor-save"]').trigger("click");
		const [payload] = w.emitted("save-funding")[0];
		expect(payload).toEqual({
			entry_id: "E1",
			budget_line: "MOH-BL-DHI-2027",
			indicative_amount: 80000000,
		});
		expect(w.find('[data-testid="dpp-editor-save"]').text()).toBe("Save funding details");
	});

	it("marks a Need as not proceeding with a reason in place of funding (PLN-AC-092)", async () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: NEED_EDITOR, pending: false, errorSummary: "" },
		});
		expect(w.find('[data-testid="dpp-f-not-proceeding-reason"]').exists()).toBe(false);
		await w.find('[data-testid="dpp-f-not-proceeding"]').setValue(true);
		expect(w.find('[data-testid="dpp-f-budget-line"]').attributes("disabled")).toBeDefined();
		await w
			.find('[data-testid="dpp-f-not-proceeding-reason"]')
			.setValue("The department will defer this requirement to the following financial year.");
		await w.find('[data-testid="dpp-editor-save"]').trigger("click");
		const [payload] = w.emitted("save-funding")[0];
		expect(payload).toEqual({
			entry_id: "E1",
			not_proceeding_reason: "The department will defer this requirement to the following financial year.",
		});
	});

	it("offers the not-proceeding control only on a Need-origin entry", () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: DIRECT_EDITOR, pending: false, errorSummary: "" },
		});
		expect(w.find('[data-testid="dpp-not-proceeding"]').exists()).toBe(false);
	});
});

describe("DppEntryEditorScreen — PLN-DES-04 (direct requirement)", () => {
	it("renders the read-only context card and exactly the eight input values", () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: DIRECT_EDITOR, pending: false, errorSummary: "" },
		});
		expect(w.find(".kt-page-title").text()).toBe("Add direct requirement");
		const context = w.find('[data-testid="dpp-editor-context"]');
		expect(context.findAll("label").map((l) => l.text())).toEqual(["Department", "Financial Year"]);
		expect(context.text()).toContain("OU-MOH-DHI — Digital Health");
		expect(w.text()).not.toContain("Procuring Entity");
		// §12.4 — units come only from enabled UOM records: no quick-create
		expect(w.find('[data-testid="dpp-unit-new"]').exists()).toBe(false);
		const editable = w
			.findAll("input, textarea, select")
			.filter((el) => el.attributes("data-testid"));
		expect(editable.map((el) => el.attributes("data-testid")).sort()).toEqual([
			"dpp-f-amount", "dpp-f-budget-line", "dpp-f-description", "dpp-f-quantity",
			"dpp-f-required-by", "dpp-f-result", "dpp-f-title", "dpp-f-unit",
		]);
	});

	it("emits save-direct with the eight values and nothing else", async () => {
		const w = mount(DppEntryEditorScreen, {
			props: { editor: DIRECT_EDITOR, pending: false, errorSummary: "" },
		});
		await w.find('[data-testid="dpp-f-title"]').setValue("Security assessment");
		await w.find('[data-testid="dpp-f-description"]').setValue("Assess and report.");
		await w.find('[data-testid="dpp-f-result"]').setValue("Actionable plan exists.");
		await w.find('[data-testid="dpp-f-quantity"]').setValue("1");
		await w.find('[data-testid="dpp-f-unit"]').setValue("UNIT-SERVICE");
		await w.find('[data-testid="dpp-f-required-by"]').setValue("2027-10-31");
		await w.find('[data-testid="dpp-f-budget-line"]').setValue("MOH-BL-DHI-2027");
		await w.find('[data-testid="dpp-f-amount"]').setValue("20000000");
		await w.find('[data-testid="dpp-editor-save"]').trigger("click");
		const [payload] = w.emitted("save-direct")[0];
		expect(payload.entry_id).toBeNull();
		expect(Object.keys(payload.values).sort()).toEqual([
			"budget_line", "description", "expected_operational_result",
			"indicative_amount", "quantity", "required_by_date", "title", "unit",
		]);
		expect(w.find('[data-testid="dpp-editor-save"]').text()).toBe("Add requirement");
	});

	it("shows the refusal summary as an alert and keeps the form", () => {
		const w = mount(DppEntryEditorScreen, {
			props: {
				editor: DIRECT_EDITOR,
				pending: false,
				errorSummary: "Select an Active Budget Line available to this department and Financial Year.",
			},
		});
		const alert = w.find('[data-testid="dpp-editor-error"]');
		expect(alert.attributes("role")).toBe("alert");
		expect(alert.text()).toContain("Select an Active Budget Line");
		expect(w.find('[data-testid="dpp-f-title"]').exists()).toBe(true);
	});
});
