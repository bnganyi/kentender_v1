// PLN-CHG-001 v1.2 §15.1(5) — FormPlanItemsDialog component tests (D9).
// PLN-DES-08: pre-checked sources, the one-each/one-combined choice only
// when several are selected, and §11.9's absences.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FormPlanItemsDialog from "./FormPlanItemsDialog.vue";

const ONE = [
	{
		dpp_entry: "DPER-1", title: "National digital health infrastructure upgrade",
		department: "Digital Health", classification: "Non-consulting services",
		quantity_display: "1 programme", amount_display: "KES 80,000,000",
	},
];

const TWO = [
	...ONE,
	{
		dpp_entry: "DPER-2", title: "Digital health platform security assessment",
		department: "Digital Health", classification: "Consulting services",
		quantity_display: "1 service", amount_display: "KES 20,000,000",
	},
];

function make(entries) {
	return mount(FormPlanItemsDialog, { props: { entries, pending: false, error: "" } });
}

describe("FormPlanItemsDialog — PLN-DES-08", () => {
	it("pre-checks every source and creates one item without a formation choice", async () => {
		const w = make(ONE);
		expect(w.find('[data-testid="pln-form-select-DPER-1"]').element.checked).toBe(true);
		expect(w.find('[data-testid="pln-form-mode-each"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toContain("Create 1 Plan Item");
		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([["DPER-1"], "each"]);
	});

	it("requires the formation choice once several sources are selected", async () => {
		const w = make(TWO);
		expect(w.find('[data-testid="pln-form-mode-each"]').element.checked).toBe(true);
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toContain("Create 2 Plan Items");
		await w.find('[data-testid="pln-form-mode-combined"]').setValue(true);
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toContain("Create 1 Plan Item");
		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([["DPER-1", "DPER-2"], "combined"]);
	});

	it("unchecking every source disables confirmation", async () => {
		const w = make(ONE);
		await w.find('[data-testid="pln-form-select-DPER-1"]').setValue(false);
		expect(w.find('[data-testid="pln-form-confirm"]').attributes("disabled")).toBeDefined();
	});

	it("carries no source search, partial quantity, amount override, lot split, Strategy, method or note (§11.9)", () => {
		const w = make(TWO);
		expect(w.find('input[type="search"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Strategic Objective");
		expect(w.text()).not.toContain("Procurement method");
		expect(w.text()).not.toContain("Note");
	});
});
