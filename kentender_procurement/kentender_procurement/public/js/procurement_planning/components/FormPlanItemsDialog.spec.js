// PLN-CHG-001 v1.23 §10.7 — FormPlanItemsDialog component tests (U08).
//
// Selected sources, the grouping choice, and what it will produce — in that
// order. The reason for combining is asked here; there is no partial quantity
// control, no implicit combining, and no way to add a source the plan can no
// longer draw on.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FormPlanItemsDialog from "./FormPlanItemsDialog.vue";

const REASON = "Both departments require the same laptop specification for the same national digital-health rollout; combining secures better unit pricing and one delivery schedule.";

function source(overrides = {}) {
	return {
		dpp_entry: "DPE-0001",
		entry_id: "DPP-MOH-HRMD-2027-002",
		title: "Clinical training laptops for digital health rollout",
		department: "Human Resources Management and Development",
		quantity: 100,
		quantity_number: "100",
		unit_label: "Each",
		amount_display: "KES 20,000,000",
		indicative_amount: 20000000,
		budget_line: "MOH-BL-HWD-2027",
		// The combinable identity the server derives from invariant 8.
		combination_key: { budget: "BUD-MOH-2027", classification: "Goods", unit: "Each", origin: "Accepted Need" },
		unavailable_reason: "",
		...overrides,
	};
}

const PAIR = [
	source(),
	source({
		dpp_entry: "DPE-0002",
		entry_id: "DPP-MOH-DH-2027-003",
		title: "Clinical deployment laptops for digital health rollout",
		department: "Digital Health",
		quantity: 150,
		quantity_number: "150",
		amount_display: "KES 30,000,000",
		indicative_amount: 30000000,
	}),
];

const make = (entries = PAIR, props = {}) =>
	mount(FormPlanItemsDialog, { props: { entries, pending: false, error: "", ...props } });

describe("FormPlanItemsDialog — U08 BASE", () => {
	it("asks the question and shows exactly what was selected", () => {
		const w = make();
		expect(w.find('[data-testid="pln-form-title"]').text()).toBe("How should these requirements be added?");
		const rows = w.findAll('[data-testid="pln-form-source-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Clinical training laptops for digital health rollout");
		expect(rows[0].text()).toContain("Human Resources Management and Development");
		expect(rows[0].text()).toContain("100");
		expect(rows[0].text()).toContain("Each");
		expect(rows[0].text()).toContain("KES 20,000,000");
		expect(rows[1].text()).toContain("Digital Health");
		expect(rows[1].text()).toContain("KES 30,000,000");
	});

	it("offers the selection as fact, not as checkboxes to re-pick", () => {
		const w = make();
		expect(w.findAll('input[type="checkbox"]')).toHaveLength(0);
	});

	it("offers only the two groupings, and no partial quantity control", () => {
		const w = make();
		expect(w.find('[data-testid="pln-form-mode-each"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-form-mode-combined"]').exists()).toBe(true);
		expect(w.findAll('input[type="number"]')).toHaveLength(0);
	});
});

describe("FormPlanItemsDialog — U08-SEPARATE", () => {
	it("previews one purchase per source, with no combination reason", () => {
		const w = make();
		expect(w.find('[data-testid="pln-form-purchases"]').text()).toBe("2");
		expect(w.find('[data-testid="pln-form-reason"]').exists()).toBe(false);
		const rows = w.findAll('[data-testid="pln-form-preview-rows"] tr');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("100 Each");
		expect(rows[1].text()).toContain("KES 30,000,000");
	});

	it("adds them without further input", async () => {
		const w = make();
		expect(w.find('[data-testid="pln-form-confirm"]').text()).toBe("Add to plan");
		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual({
			dppEntries: ["DPE-0001", "DPE-0002"],
			mode: "each",
			combinationReason: "",
			combinedTitle: "",
		});
	});
});

describe("FormPlanItemsDialog — U08-COMBINE", () => {
	async function combining() {
		const w = make();
		await w.find('[data-testid="pln-form-mode-combined"]').setValue();
		return w;
	}

	it("requires the reason before the purchase can be added", async () => {
		const w = await combining();
		expect(w.find('[data-testid="pln-form-confirm"]').attributes("disabled")).toBeDefined();

		await w.find('[data-testid="pln-form-reason"]').setValue("Too short");
		expect(w.find('[data-testid="pln-form-confirm"]').attributes("disabled")).toBeDefined();

		await w.find('[data-testid="pln-form-reason"]').setValue(REASON);
		expect(w.find('[data-testid="pln-form-confirm"]').attributes("disabled")).toBeUndefined();
	});

	it("previews one purchase with the combined quantity, cost and title", async () => {
		const w = await combining();
		await w.find('[data-testid="pln-form-reason"]').setValue(REASON);
		await w.find('[data-testid="pln-form-title-input"]').setValue(
			"Clinical training and deployment laptops for digital health rollout",
		);
		const preview = w.find('[data-testid="pln-form-preview"]');
		expect(w.find('[data-testid="pln-form-purchases"]').text()).toBe("1");
		expect(preview.text()).toContain("250 Each");
		expect(preview.text()).toContain("KES 50,000,000");
		expect(w.find('[data-testid="pln-form-preview-title"]').text()).toBe(
			"Clinical training and deployment laptops for digital health rollout",
		);

		await w.find('[data-testid="pln-form-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual({
			dppEntries: ["DPE-0001", "DPE-0002"],
			mode: "combined",
			combinationReason: REASON,
			combinedTitle: "Clinical training and deployment laptops for digital health rollout",
		});
	});

	it("never adds two different units into one number", async () => {
		// Two units never combine under invariant 8, so this is the display
		// rule alone: even asked directly, the numbers stay apart.
		const w = make([PAIR[0], source({ dpp_entry: "DPE-0003", quantity: 2, quantity_number: "2", unit_label: "Programme", indicative_amount: 5000000, amount_display: "KES 5,000,000" })]);
		await w.find('[data-testid="pln-form-mode-combined"]').setValue();
		expect(w.find('[data-testid="pln-form-preview"]').text()).toContain("100 Each + 2 Programme");
		expect(w.find('[data-testid="pln-form-preview"]').text()).not.toContain("102");
	});
});

describe("FormPlanItemsDialog — U08-INCOMPATIBLE", () => {
	it("says why, disables only the combine option, and still adds separately", async () => {
		const w = make([
			PAIR[0],
			source({
				dpp_entry: "DPE-0004",
				budget_line: "MOH-BL-DHP-2027",
				combination_key: { budget: "BUD-MOH-DEV-2027", classification: "Goods", unit: "Each", origin: "Accepted Need" },
			}),
		]);
		// The governed sentence, plus the difference that actually blocks it.
		expect(w.find('[data-testid="pln-form-incompatible"]').text()).toBe(
			"These requirements cannot be combined. Add them as separate purchases. They draw on different budgets.",
		);
		expect(w.find('[data-testid="pln-form-mode-combined"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pln-form-mode-each"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="pln-form-confirm"]').attributes("disabled")).toBeUndefined();
	});
});

describe("FormPlanItemsDialog — U08-DUPLICATE/INCOMPLETE", () => {
	it("names the source and its problem, and offers no way to add it", () => {
		const w = make([
			PAIR[0],
			source({
				dpp_entry: "DPE-0005",
				title: "National digital health infrastructure upgrade",
				unavailable_reason: "is already held by a purchase whose scope was fixed by an authorised requisition.",
			}),
		]);
		expect(w.find('[data-testid="pln-form-blocked"]').text()).toContain(
			"National digital health infrastructure upgrade is already held by a purchase",
		);
		expect(w.find('[data-testid="pln-form-confirm"]').exists()).toBe(false);
		// The choice is not offered either: there is nothing to choose between.
		expect(w.find('[data-testid="pln-form-mode-each"]').exists()).toBe(false);
	});
});
