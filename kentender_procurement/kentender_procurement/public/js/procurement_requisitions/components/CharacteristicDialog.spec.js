// REQ-DES-05's "Add characteristic" dialog (§13.7) — the required-value
// control switches on the selected characteristic's own catalogue control
// type; the dialog validates only the common case, the server re-checks.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CharacteristicDialog from "./CharacteristicDialog.vue";

const EDITOR = {
	package: {
		items: [
			{ requisition_item_id: "RQI-001", item_name: "Business laptops", plan_item_line_id: "DL-001", equipment_category: "Laptop" },
		],
	},
	catalogue: {
		characteristics: [
			{ key: "electrical_compatibility", label: "Electrical compatibility", applies_to: null, control: "YES_NO", comparison: "Required", unit: "", options: ["Yes"] },
			{ key: "memory", label: "Memory", applies_to: ["Laptop", "Desktop computer", "Tablet"], control: "INTEGER", comparison: "Minimum", unit: "GB", options: [], minimum: 1, maximum: 512 },
			{ key: "storage_type", label: "Storage type", applies_to: ["Laptop", "Desktop computer", "Tablet"], control: "SELECT", comparison: "One of", unit: "", options: ["NVMe SSD", "SSD", "eMMC"], allows_other: false },
			{ key: "network_connectivity", label: "Network connectivity", applies_to: ["Laptop", "Desktop computer", "Tablet"], control: "MULTI_SELECT", comparison: "Required", unit: "", options: ["Wi-Fi 6", "Bluetooth 5 or later"] },
			{ key: "required_ports", label: "Required ports", applies_to: ["Laptop", "Desktop computer", "Tablet"], control: "PORT_LIST", comparison: "Required", unit: "", port_options: ["USB-A", "USB-C"] },
			{ key: "other_essential_characteristic", label: "Other essential characteristic", applies_to: null, control: "TEXT", comparison: "Minimum", unit: "", min_length: 3, max_length: 200, allows_other: true },
			{ key: "print_speed", label: "Print speed", applies_to: ["Printer"], control: "INTEGER", comparison: "Minimum", unit: "pages per minute" },
		],
	},
};

function make(overrides = {}) {
	return mount(CharacteristicDialog, { props: { editor: { ...EDITOR, ...overrides }, pending: false, error: "" } });
}

describe("CharacteristicDialog — REQ-DES-05", () => {
	it("offers only the item and All items in the Applies-to select", () => {
		const w = make();
		const options = w.find("#ch-applies-to").findAll("option").map((o) => o.text());
		expect(options).toEqual(["All items", "Business laptops — DL-001"]);
	});

	it("offers only characteristics applicable to an equipment category on this Draft", () => {
		const w = make();
		const options = w.find("#ch-key").findAll("option").map((o) => o.text());
		expect(options).toContain("Electrical compatibility");
		expect(options).toContain("Memory");
		expect(options).not.toContain("Print speed");
	});

	it("renders a Yes/No control for a YES_NO characteristic and submits its value", async () => {
		const w = make();
		await w.find("#ch-key").setValue("electrical_compatibility");
		await w.findAll('input[type="radio"]')[0].setValue(true);
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.characteristic_key).toBe("electrical_compatibility");
		expect(payload.value).toBe("Yes");
		expect(payload.applies_to_scope).toBe("All items");
	});

	it("renders a number control for an INTEGER characteristic", async () => {
		const w = make();
		await w.find("#ch-key").setValue("memory");
		await w.find("#ch-value").setValue(16);
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0].value).toBe("16");
	});

	it("submits Item scope and id when a specific item is selected", async () => {
		const w = make();
		await w.find("#ch-applies-to").setValue("RQI-001");
		await w.find("#ch-key").setValue("memory");
		await w.find("#ch-value").setValue(16);
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.applies_to_scope).toBe("Item");
		expect(payload.applies_to_id).toBe("RQI-001");
	});

	it("renders checkboxes for a MULTI_SELECT characteristic and submits every checked value", async () => {
		const w = make();
		await w.find("#ch-key").setValue("network_connectivity");
		const checkboxes = w.findAll('input[type="checkbox"]');
		await checkboxes[0].setValue(true);
		await checkboxes[1].setValue(true);
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0].value).toEqual(["Wi-Fi 6", "Bluetooth 5 or later"]);
	});

	it("renders a repeatable port row for a PORT_LIST characteristic and can add another", async () => {
		const w = make();
		await w.find("#ch-key").setValue("required_ports");
		expect(w.findAll(".req-port-row")).toHaveLength(1);
		await w.find(".req-port-row select").setValue("USB-C");
		await w.find(".req-port-row input").setValue(2);
		await w.find(".req-port-row + button").trigger("click");
		expect(w.findAll(".req-port-row")).toHaveLength(2);
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0].value[0]).toEqual({ port_type: "USB-C", minimum_count: 2 });
	});

	it("requires a 20-300 character reason only for Other essential characteristic", async () => {
		const w = make();
		await w.find("#ch-key").setValue("other_essential_characteristic");
		await w.find("#ch-value").setValue("A specific requirement not covered elsewhere in the catalogue.");
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.find(".req-field-error").exists()).toBe(true);
		await w.find("#ch-reason").setValue("This is a genuinely distinct requirement the released catalogue has no entry for.");
		await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeTruthy();
	});

	it("emits cancel", async () => {
		const w = make();
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});

	describe("confirming an existing value-less Proposed row", () => {
		function makeWithPrefill() {
			return mount(CharacteristicDialog, {
				props: {
					editor: EDITOR,
					pending: false,
					error: "",
					prefillRow: { technical_requirement_id: "TECH-003", characteristic_key: "memory", applies_to_scope: "All items", applies_to_id: "" },
				},
			});
		}

		it("locks Applies-to and Characteristic to the row's own values and relabels the dialog", () => {
			const w = makeWithPrefill();
			expect(w.find(".kt-dialog-title").text()).toBe("Confirm characteristic");
			expect(w.find("#ch-key").element.value).toBe("memory");
			expect(w.find("#ch-key").element.disabled).toBe(true);
			expect(w.find("#ch-applies-to").element.disabled).toBe(true);
			expect(w.find('[data-testid="req-characteristic-dialog-confirm"]').text()).toBe("Confirm");
		});

		it("submits the supplied value without requiring the user to re-pick the characteristic", async () => {
			const w = makeWithPrefill();
			await w.find("#ch-value").setValue(16);
			await w.find('[data-testid="req-characteristic-dialog-confirm"]').trigger("click");
			const payload = w.emitted("confirm")[0][0];
			expect(payload.characteristic_key).toBe("memory");
			expect(payload.value).toBe("16");
		});
	});
});
