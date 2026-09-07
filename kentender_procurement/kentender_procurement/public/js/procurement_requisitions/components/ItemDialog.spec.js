// The "Add equipment item" dialog (§13.6): required fields, the read-only
// Unit control, validation before emitting confirm, and pre-filled editing
// of an existing item.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ItemDialog from "./ItemDialog.vue";

const EDITOR = {
	drawdown_context: [
		{ drawdown_line_id: "DL-001", organisation_unit_label: "Human Resources Management and Development", source_title: "Business laptops" },
		{ drawdown_line_id: "DL-002", organisation_unit_label: "Digital Health", source_title: "Business laptops" },
	],
	catalogue: { equipment_categories: ["Laptop", "Desktop computer", "Monitor"] },
	delivery_locations: [{ name: "MOH-HQ", location_name: "Ministry of Health Headquarters, Afya House, Nairobi" }],
};

function make(overrides = {}) {
	return mount(ItemDialog, { props: { editor: EDITOR, item: null, pending: false, error: "", ...overrides } });
}

describe("ItemDialog — §13.6", () => {
	it("renders Add equipment item with a read-only Unit of Each", () => {
		const w = make();
		expect(w.find(".kt-dialog-title").text()).toBe("Add equipment item");
		expect(w.find("#item-unit").element.value).toBe("Each");
		expect(w.find("#item-unit").attributes("disabled")).toBeDefined();
	});

	it("restricts Planning source options to this Requisition's own drawdown lines", () => {
		const w = make();
		const options = w.find("#item-source").findAll("option").filter((o) => o.attributes("value"));
		expect(options.map((o) => o.text())).toEqual([
			"Human Resources Management and Development — Business laptops",
			"Digital Health — Business laptops",
		]);
	});

	it("refuses to confirm with required fields missing and shows inline errors, never a popup", async () => {
		const w = make();
		await w.find('[data-testid="req-item-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeUndefined();
		expect(w.text()).toContain("A Planning source is required.");
		expect(w.text()).toContain("An equipment category is required.");
		expect(w.text()).toContain("An item name is required.");
		expect(w.text()).toContain("Intended use is required.");
	});

	it("emits confirm with every field once all required fields are filled", async () => {
		const w = make();
		await w.find("#item-source").setValue("DL-001");
		await w.find("#item-category").setValue("Laptop");
		await w.find("#item-name").setValue("Business laptops");
		await w.find("#item-quantity").setValue(100);
		await w.find("#item-use").setValue("Clinical training for Human Resources Management and Development staff");
		await w.find("#item-location").setValue("MOH-HQ");
		await w.find("#item-date").setValue("2027-09-30");
		await w.find('[data-testid="req-item-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual({
			plan_item_line_id: "DL-001",
			equipment_category: "Laptop",
			item_name: "Business laptops",
			quantity: 100,
			intended_use: "Clinical training for Human Resources Management and Development staff",
			delivery_location: "MOH-HQ",
			latest_delivery_date: "2027-09-30",
		});
	});

	it("pre-fills every field and titles itself Edit equipment item when editing an existing row", () => {
		const w = make({
			item: {
				requisition_item_id: "RQI-001", plan_item_line_id: "DL-001", equipment_category: "Laptop", item_name: "Business laptops",
				quantity: 100, intended_use: "Clinical training", delivery_location: "MOH-HQ", latest_delivery_date: "2027-09-30",
			},
		});
		expect(w.find(".kt-dialog-title").text()).toBe("Edit equipment item");
		expect(w.find("#item-name").element.value).toBe("Business laptops");
		expect(w.find('[data-testid="req-item-dialog-confirm"]').text()).toBe("Save changes");
	});

	it("emits cancel and shows a server-returned error inline", async () => {
		const w = make({ error: "Another user changed this Requisition. Reload before continuing." });
		expect(w.text()).toContain("Another user changed this Requisition. Reload before continuing.");
		await w.find(".kt-dialog-actions button").trigger("click");
		expect(w.emitted("cancel")).toHaveLength(1);
	});
});
