// REQ-DES-04 Step 2: Equipment items (§13.6/§13.6A) — the item table, the
// Add equipment item button, and one baseline-proposal banner per item,
// each row independently Confirm/Remove-able while still "Proposed".
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StepItems from "./StepItems.vue";

const EDITOR = {
	package: {
		items: [
			{ requisition_item_id: "RQI-001", plan_item_line_id: "DL-001", equipment_category: "Laptop", item_name: "Business laptops", quantity: 100, unit: "Each", intended_use: "Clinical training for Human Resources Management and Development staff", delivery_location: "Nairobi", latest_delivery_date: "2027-09-30" },
			{ requisition_item_id: "RQI-002", plan_item_line_id: "DL-002", equipment_category: "Laptop", item_name: "Business laptops", quantity: 150, unit: "Each", intended_use: "Field digital-health deployment for Digital Health staff", delivery_location: "Nairobi", latest_delivery_date: "2027-09-30" },
		],
		technical_requirements: [
			{ technical_requirement_id: "TECH-001", applies_to_id: "RQI-001", characteristic_key: "electrical_compatibility", comparison: "Required", required_value_json: '{"value":"Yes"}', row_status: "Proposed" },
			{ technical_requirement_id: "TECH-002", applies_to_id: "RQI-001", characteristic_key: "new_unused_equipment", comparison: "Required", required_value_json: '{"value":"Yes"}', row_status: "Proposed" },
			{ technical_requirement_id: "TECH-003", applies_to_id: "RQI-001", characteristic_key: "memory", comparison: "Minimum", required_value_json: "", row_status: "Proposed" },
			{ technical_requirement_id: "TECH-004", applies_to_id: "RQI-001", characteristic_key: "storage_type", comparison: "One of", required_value_json: '{"value":"NVMe SSD"}', row_status: "Confirmed" },
		],
	},
	catalogue: {
		characteristics: [
			{ key: "electrical_compatibility", label: "Electrical compatibility" },
			{ key: "new_unused_equipment", label: "New and unused equipment" },
			{ key: "memory", label: "Memory" },
			{ key: "storage_type", label: "Storage type" },
		],
	},
};

function make(overrides = {}) {
	return mount(StepItems, { props: { editor: { ...EDITOR, ...overrides } } });
}

describe("StepItems — REQ-DES-04", () => {
	it("renders the item table with the exact headers and two rows", () => {
		const w = make();
		const table = w.find('[data-testid="req-items-table"]');
		expect(table.findAll("thead th").map((th) => th.text())).toEqual(["Item", "Planning source", "Category", "Quantity", "Intended use", "Delivery", ""]);
		const rows = w.findAll('[data-testid="req-items-table"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Business laptops");
		expect(rows[0].text()).toContain("DL-001");
		expect(rows[0].text()).toContain("100 Each");
		expect(rows[0].text()).toContain("Clinical training for Human Resources Management and Development staff");
	});

	it("emits add-item from the header button", async () => {
		const w = make();
		await w.find('[data-testid="req-add-item"]').trigger("click");
		expect(w.emitted("add-item")).toHaveLength(1);
	});

	it("emits edit-item and remove-item with the exact row", async () => {
		const w = make();
		const row = w.findAll('[data-testid="req-items-table"] tbody tr')[0];
		const links = row.findAll("a");
		await links[0].trigger("click");
		expect(w.emitted("edit-item")[0][0].requisition_item_id).toBe("RQI-001");
		await links[1].trigger("click");
		expect(w.emitted("remove-item")[0][0].requisition_item_id).toBe("RQI-001");
	});

	it("shows one baseline banner naming only the value-bearing Proposed rows, per item", () => {
		const w = make();
		const banner = w.find('[data-testid="req-baseline-banner-RQI-001"]');
		expect(banner.text()).toContain("2 baseline characteristics proposed");
		expect(banner.text()).toContain("Business laptops (DL-001)");
		const rows = banner.findAll("tbody tr");
		expect(rows).toHaveLength(2); // TECH-001/002 only — TECH-003 has no value, TECH-004 is already Confirmed
		expect(rows[0].text()).toContain("Electrical compatibility");
		expect(rows[0].find(".kt-status").text()).toBe("Proposed");
		expect(rows[0].text()).toContain("Yes");
		expect(w.find('[data-testid="req-baseline-banner-RQI-002"]').exists()).toBe(false);
	});

	it("emits confirm-requirement and remove-requirement with the exact row", async () => {
		const w = make();
		const banner = w.find('[data-testid="req-baseline-banner-RQI-001"]');
		await banner.find('[data-testid="req-confirm-TECH-001"]').trigger("click");
		expect(w.emitted("confirm-requirement")[0][0].technical_requirement_id).toBe("TECH-001");
		const row = banner.findAll("tbody tr")[0];
		await row.findAll("a")[1].trigger("click");
		expect(w.emitted("remove-requirement")[0][0].technical_requirement_id).toBe("TECH-001");
	});

	it("omits every banner once nothing is left Proposed", () => {
		const w = make({
			package: {
				...EDITOR.package,
				technical_requirements: EDITOR.package.technical_requirements.map((r) => ({ ...r, row_status: "Confirmed" })),
			},
		});
		expect(w.find(".req-baseline-intro").exists()).toBe(false);
	});
});
