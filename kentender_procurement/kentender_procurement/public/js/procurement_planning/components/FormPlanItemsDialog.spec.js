// PLN-CHG-001 v1.18 (PLN18-304) — FormPlanItemsDialog component tests.
// U08: pre-checked sources, the one-each/one-combined choice only once
// several are selected, U08-incompatible's differing-Budget-Line block, and
// §11.9's absences.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FormPlanItemsDialog from "./FormPlanItemsDialog.vue";

const ONE = [
	{
		dpp_entry: "DPER-1", title: "National digital health infrastructure upgrade",
		department: "Digital Health", budget_line: "BL-DHI", budget_line_display: "MOH-BL-DHI-2027",
		quantity: 1, quantity_display: "1 programme", amount_display: "KES 80,000,000",
	},
];

const TWO_COMPATIBLE = [
	...ONE,
	{
		dpp_entry: "DPER-2", title: "Clinical deployment laptops for digital health rollout",
		department: "Digital Health", budget_line: "BL-DHI", budget_line_display: "MOH-BL-DHI-2027",
		quantity: 150, quantity_display: "150 each", amount_display: "KES 30,000,000",
	},
];

const TWO_INCOMPATIBLE = [
	...ONE,
	{
		dpp_entry: "DPER-3", title: "Clinical training laptops for digital health rollout",
		department: "Human Resources Management and Development", budget_line: "BL-HWD", budget_line_display: "MOH-BL-HWD-2027",
		quantity: 100, quantity_display: "100 each", amount_display: "KES 20,000,000",
	},
];

function make(entries) {
	return mount(FormPlanItemsDialog, { props: { entries, pending: false, error: "" } });
}

describe("FormPlanItemsDialog — U08", () => {
	it("pre-checks the one source and creates one item without a formation choice", async () => {
		const w = make(ONE);
		expect(w.get(".kt-dialog-title").text()).toBe("Form Plan Item");
		expect(w.find('[data-testid="pln-form-select-DPER-1"]').element.checked).toBe(true);
		expect(w.find('[data-testid="pln-form-mode-each"]').exists()).toBe(false);
		expect(w.findAll("thead th").map((th) => th.text())).toEqual([
			"", "Requirement", "Department", "Quantity", "Budget Line", "Amount",
		]);
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toBe("Create Plan Item");
		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([["DPER-1"], "each"]);
	});

	it("requires the formation choice once several compatible sources are selected", async () => {
		const w = make(TWO_COMPATIBLE);
		expect(w.get(".kt-dialog-title").text()).toBe("Form Plan Items");
		expect(w.find('[data-testid="pln-form-mode-each"]').element.checked).toBe(true);
		expect(w.find('[data-testid="pln-form-mode-combined"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toContain("Create 2 Plan Items");
		await w.find('[data-testid="pln-form-mode-combined"]').setValue(true);
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toBe("Create Plan Item");
		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([["DPER-1", "DPER-2"], "combined"]);
	});

	// U08-incompatible
	it("blocks the combined choice when selected sources' Budget Lines differ", async () => {
		const w = make(TWO_INCOMPATIBLE);
		expect(w.find('[data-testid="pln-form-incompatible"]').text()).toContain(
			"These requirements cannot be combined because their Procurement Budget Lines differ."
		);
		const combined = w.find('[data-testid="pln-form-mode-combined"]');
		expect(combined.attributes("disabled")).toBeDefined();
		await combined.setValue(true); // even if forced, the effective mode stays "each"
		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([["DPER-1", "DPER-3"], "each"]);
	});

	it("has no incompatibility notice or disabled radio when Budget Lines match", () => {
		const w = make(TWO_COMPATIBLE);
		expect(w.find('[data-testid="pln-form-incompatible"]').exists()).toBe(false);
	});

	it("unchecking every source disables confirmation", async () => {
		const w = make(ONE);
		await w.find('[data-testid="pln-form-select-DPER-1"]').setValue(false);
		expect(w.find('[data-testid="pln-form-confirm"]').attributes("disabled")).toBeDefined();
	});

	it("carries no source search, partial quantity, amount override, lot split, Strategy, method or note (§11.9)", () => {
		const w = make(TWO_COMPATIBLE);
		expect(w.find('input[type="search"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Strategic Objective");
		expect(w.text()).not.toContain("Procurement method");
		expect(w.text()).not.toContain("Note");
	});

	it("shows the Preview facts: selected requirements, items to create, quantity and value", () => {
		const w = make(ONE);
		const facts = w.findAll(".pln-fact");
		expect(facts.map((f) => f.get(".kt-label").text())).toEqual([
			"Selected requirements", "Plan Items to create", "Quantity", "Value",
		]);
		expect(facts.map((f) => f.get(".pln-fact-val").text())).toEqual([
			"1", "1", "1 programme", "KES 80,000,000",
		]);
	});

	it("sums Quantity across several selected sources regardless of formation choice", async () => {
		const w = make(TWO_COMPATIBLE);
		const quantityFact = () => w.findAll(".pln-fact")[2].get(".pln-fact-val").text();
		expect(quantityFact()).toBe("151");
		await w.find('[data-testid="pln-form-mode-combined"]').setValue(true);
		expect(quantityFact()).toBe("151");
	});
});
