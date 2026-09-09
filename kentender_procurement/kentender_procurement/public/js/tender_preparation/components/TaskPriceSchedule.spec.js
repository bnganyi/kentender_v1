// §8.3 / TPR-AC-013 — generated schedule, no officer input, no authorised value.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import TaskPriceSchedule from "./TaskPriceSchedule.vue";

describe("TaskPriceSchedule — §8.3", () => {
	it("renders one generated row per grouped line with supplier placeholders and no input", () => {
		const editor = { generated: { price_schedule: { rows: [{ line: 1, description: "Business laptops", quantity: 250, unit: "Each", unit_price: "[Tenderer to complete]", tax: "[Tenderer to complete]", line_total: "[Tenderer to complete]" }], tender_total: "[Tenderer to complete]" } }, inherited: { authorised_value: "KES 50,000,000.00" } };
		const w = mount(TaskPriceSchedule, { props: { editor } });
		expect(w.findAll("tbody tr").length).toBe(1);
		expect(w.findAll("th").map((h) => h.text())).toEqual(["Item", "Qty", "Unit", "Unit price", "Tax", "Line total"]);
		expect(w.findAll("input, select, textarea").length).toBe(0);
		expect(w.text()).not.toContain("50,000,000");
		expect(w.text()).toContain("The authorised internal value is not copied into this schedule.");
	});
});
