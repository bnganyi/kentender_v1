// PLN-CHG-001 v1.23 §10.4 — EntryFundingPanel component tests (U03-FUNDING).
//
// Just enough of the requirement to know which one it is, the two fields the
// department actually owns, and a plain statement of where a correction to the
// requirement itself has to go.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import EntryFundingPanel from "./EntryFundingPanel.vue";

function editor(overrides = {}) {
	return {
		outcome: "OK",
		dpp_version: "DPPV-MOH-01441-2027-001-V1",
		record_version: 3,
		mutable: true,
		can_edit: true,
		currency: "KES",
		budget_lines: [
			{ id: "BL-1", reference: "MOH-BL-DHI-2027", title: "Digital health infrastructure programme", label: "MOH-BL-DHI-2027 — Digital health infrastructure programme" },
			{ id: "BL-2", reference: "MOH-BL-HWD-2027", title: "Digital health workforce development", label: "MOH-BL-HWD-2027 — Digital health workforce development" },
		],
		entry: {
			entry_id: "DPPE-MOH-DH-2027-001",
			title: "National digital health infrastructure upgrade",
			description: "Upgrade the national digital health infrastructure.",
			expected_operational_result: "The national platform runs on supported infrastructure.",
			quantity: 1,
			quantity_display: "1 programme",
			unit_label: "Programme",
			required_by_display: "31 Aug 2027",
			budget_line: "",
			indicative_amount: null,
		},
		...overrides,
	};
}

const make = (props = {}) =>
	mount(EntryFundingPanel, {
		props: { editor: editor(), budgetLine: "", amount: "", pending: false, error: "", ...props },
	});

describe("EntryFundingPanel — U03-FUNDING", () => {
	it("summarises the requirement without repeating all of it", () => {
		const summary = make().find('[data-testid="dpp-funding-summary"]').text();
		expect(summary).toContain("National digital health infrastructure upgrade");
		expect(summary).toContain("1 programme");
		expect(summary).toContain("31 Aug 2027");
		// The rest is behind the disclosure, not in the summary.
		expect(summary).not.toContain("The national platform runs on supported infrastructure.");
	});

	it("keeps the full six requirement facts one disclosure away", () => {
		const details = make().find('[data-testid="dpp-funding-requirement-details"]');
		expect(details.attributes("open")).toBeUndefined();
		const text = details.text();
		expect(text).toContain("Upgrade the national digital health infrastructure.");
		expect(text).toContain("The national platform runs on supported infrastructure.");
		expect(text).toContain("Programme");
	});

	it("offers the budget line by name with its code beneath", async () => {
		const w = make({ budgetLine: "BL-1" });
		const options = w.findAll('[data-testid="dpp-funding-line"] option').map((o) => o.text());
		expect(options).toContain("Digital health infrastructure programme");
		expect(w.find('[data-testid="dpp-funding-line-code"]').text()).toBe("MOH-BL-DHI-2027");
	});

	it("says what the cost must include, where the cost is entered", () => {
		expect(make().find('[data-testid="dpp-funding-amount-hint"]').text()).toBe(
			"Enter the full estimated cost, including applicable delivery and other incidental costs.",
		);
	});

	it("binds the inputs to the caller's own draft, not the server echo", async () => {
		const w = make();
		await w.find('[data-testid="dpp-funding-amount"]').setValue("80000000");
		expect(w.emitted("update:amount")[0][0]).toBe("80000000");
		await w.find('[data-testid="dpp-funding-line"]').setValue("BL-1");
		expect(w.emitted("update:budgetLine")[0][0]).toBe("BL-1");
	});

	it("will not save until both facts are there", async () => {
		expect(make().find('[data-testid="dpp-funding-save"]').attributes("disabled")).toBeDefined();
		expect(make({ budgetLine: "BL-1" }).find('[data-testid="dpp-funding-save"]').attributes("disabled")).toBeDefined();
		expect(make({ budgetLine: "BL-1", amount: "0" }).find('[data-testid="dpp-funding-save"]').attributes("disabled")).toBeDefined();

		const complete = make({ budgetLine: "BL-1", amount: "80000000" });
		expect(complete.find('[data-testid="dpp-funding-save"]').attributes("disabled")).toBeUndefined();
		await complete.find('[data-testid="dpp-funding-save"]').trigger("click");
		expect(complete.emitted("save")).toHaveLength(1);
	});

	it("names where a correction to the requirement itself has to go", () => {
		const text = make().find('[data-testid="dpp-funding-correct-source"]').text();
		expect(text).toContain("Correct the source requirement");
		expect(text).toContain("Source changes require their own Departmental Needs review.");
	});

	it("offers exclusion as its own action, not as a third field", async () => {
		const w = make();
		expect(w.find('[data-testid="dpp-funding-exclude"]').text()).toBe("Exclude from this year's departmental plan");
		await w.find('[data-testid="dpp-funding-exclude"]').trigger("click");
		expect(w.emitted("exclude")).toHaveLength(1);
	});
});

describe("EntryFundingPanel — a reader who cannot edit", () => {
	it("keeps every fact and offers no control", () => {
		const w = make({ editor: editor({ can_edit: false }) });
		expect(w.find('[data-testid="dpp-funding-summary"]').text()).toContain("National digital health infrastructure upgrade");
		expect(w.find('[data-testid="dpp-funding-save"]').exists()).toBe(false);
		expect(w.find('[data-testid="dpp-funding-exclude"]').exists()).toBe(false);
		expect(w.find('[data-testid="dpp-funding-line"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="dpp-funding-amount"]').attributes("disabled")).toBeDefined();
	});
});
