// Release 1.4 row-group control: a bounded table with per-cell refusals, a running total and
// a read-only form for a table the Account supplies.
import { afterEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import RowGroupControl from "./RowGroupControl.vue";

const TABLE = {
	columns: [
		{ key: "name", label: "Name", type: "text" },
		{ key: "shares", label: "Shares owned (%)", type: "decimal" },
		{ key: "kind", label: "Kind", type: "choice", options: ["Director", "Partner"] },
	],
	minimum_rows: 1, maximum_rows: 3, totals: [{ column: "shares", equals: "100" }],
};
const FIELD = { handle: "h-owners", kind: "row_group", label: "Owners", help: "", editable: true, visible: true, required: true, value: null, issue: null, row_group: TABLE };
const mountIt = (props) => mount(RowGroupControl, { props: { field: FIELD, ...props }, attachTo: document.body, global: { config: { globalProperties: { __: globalThis.__ } } } });
afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("A row-group field", () => {
	it("starts with one blank row and emits the whole table as it is edited", async () => {
		const wrapper = mountIt({});
		expect(wrapper.findAll('[data-testid="bds-rowgroup-row-h-owners"]')).toHaveLength(1);
		await wrapper.get('[data-testid="bds-cell-h-owners-0-name"]').setValue("Mary");
		expect(wrapper.emitted("update:modelValue")[0][0]).toEqual([{ name: "Mary", shares: "", kind: "" }]);
	});

	it("adds rows up to the published limit and then says the table is full", async () => {
		const rows = [{ name: "A", shares: "50", kind: "Director" }, { name: "B", shares: "30", kind: "Director" }];
		const wrapper = mountIt({ modelValue: rows });
		await wrapper.get('[data-testid="bds-rowgroup-add-h-owners"]').trigger("click");
		expect(wrapper.emitted("update:modelValue")[0][0]).toHaveLength(3);
		await wrapper.setProps({ modelValue: [...rows, { name: "C", shares: "", kind: "" }] });
		const add = wrapper.get('[data-testid="bds-rowgroup-add-h-owners"]');
		expect(add.attributes("disabled")).toBeDefined();
		expect(add.text()).toBe("Table is full");
	});

	it("shows the running total against the published figure", () => {
		const wrapper = mountIt({ modelValue: [{ name: "A", shares: "60", kind: "" }, { name: "B", shares: "30.5", kind: "" }] });
		expect(wrapper.get('[data-testid="bds-rowgroup-total-h-owners"]').text()).toBe("Shares owned (%) added up: 90.5 of 100");
	});

	it("names a refused cell and a refused table in place and keeps the entry", () => {
		const errors = { "h-owners.0.shares": "Enter a number." };
		const wrapper = mountIt({ modelValue: [{ name: "A", shares: "sixty", kind: "" }], errors, issue: "Shares owned (%) must add up to 100; they add up to 0.00." });
		expect(wrapper.get('[data-testid="bds-cell-h-owners-0-shares"]').attributes("aria-invalid")).toBe("true");
		expect(wrapper.get('[data-testid="bds-cell-h-owners-0-shares"]').element.value).toBe("sixty");
		expect(wrapper.text()).toContain("Enter a number.");
		expect(wrapper.get('[data-testid="bds-rowgroup-error-h-owners"]').text()).toContain("must add up to 100");
	});

	it("keeps the only row of a required table and lets any other row go", async () => {
		const one = mountIt({ modelValue: [{ name: "A", shares: "100", kind: "" }] });
		expect(one.get('[data-testid="bds-rowgroup-remove-h-owners-0"]').attributes("disabled")).toBeDefined();
		const two = mountIt({ modelValue: [{ name: "A", shares: "60", kind: "" }, { name: "B", shares: "40", kind: "" }] });
		await two.get('[data-testid="bds-rowgroup-remove-h-owners-1"]').trigger("click");
		expect(two.emitted("update:modelValue")[0][0]).toEqual([{ name: "A", shares: "60", kind: "" }]);
	});

	it("is read-only when the Account supplies it, as a table at desktop width and cards when narrow", () => {
		const supplied = { ...FIELD, editable: false, supplied_from: "account" };
		const rows = [{ name: "Mary Wanjiku", shares: "100.00", kind: "Director" }];
		const desktop = mountIt({ field: supplied, modelValue: rows, disabled: true });
		expect(desktop.find("input").exists()).toBe(false);
		expect(desktop.get('[data-testid="bds-rowgroup-table-h-owners"]').text()).toContain("Mary Wanjiku");
		expect(desktop.text()).toContain("From your Account; change it there.");
		globalThis.__narrow = true;
		const narrow = mountIt({ field: supplied, modelValue: rows, disabled: true });
		expect(narrow.find("table").exists()).toBe(false);
		expect(narrow.text()).toContain("Mary Wanjiku");
	});

	it("offers a choice column as a select of its options", async () => {
		const wrapper = mountIt({ modelValue: [{ name: "A", shares: "", kind: "" }] });
		const select = wrapper.get('[data-testid="bds-cell-h-owners-0-kind"]');
		expect(select.findAll("option").map((o) => o.text())).toEqual(["Select", "Director", "Partner"]);
		await select.setValue("Partner");
		expect(wrapper.emitted("update:modelValue")[0][0][0].kind).toBe("Partner");
	});
});
