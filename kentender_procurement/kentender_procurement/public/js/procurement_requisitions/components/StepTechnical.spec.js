// REQ-DES-05 Step 3: Technical and support (§13.7) — tabs, the technical
// characteristics table (Confirmed and still-Proposed rows), and the
// warranty-and-support panel.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StepTechnical from "./StepTechnical.vue";

const EDITOR = {
	package: {
		record_version: 1,
		minimum_warranty_months: 36,
		onsite_support_required: true,
		maximum_support_response_hours: 8,
		manufacturer_support_required: true,
		service_location_constraint: "Within Kenya",
		support_description: "Supplier to provide escalation and warranty-contact details.",
		items: [
			{ requisition_item_id: "RQI-001", item_name: "Business laptops" },
			{ requisition_item_id: "RQI-002", item_name: "Business laptops" },
		],
		technical_requirements: [
			{ technical_requirement_id: "TECH-001", applies_to_scope: "All items", applies_to_id: "", characteristic_key: "electrical_compatibility", comparison: "Required", unit: "", required_value_json: '{"value":"Yes"}', required_value_display: "Yes", row_status: "Confirmed" },
			{ technical_requirement_id: "TECH-002", applies_to_scope: "Item", applies_to_id: "RQI-001", characteristic_key: "memory", comparison: "Minimum", unit: "GB", required_value_json: "", required_value_display: "", row_status: "Proposed" },
		],
	},
	catalogue: {
		characteristics: [
			{ key: "electrical_compatibility", label: "Electrical compatibility" },
			{ key: "memory", label: "Memory" },
		],
	},
};

function make(overrides = {}) {
	return mount(StepTechnical, { props: { editor: { ...EDITOR, ...overrides } } });
}

describe("StepTechnical — REQ-DES-05", () => {
	it("renders one tab per distinct item name, deduplicating two rows sharing a name", () => {
		const w = make();
		const labels = w.findAll('[role="tablist"] .req-seg-opt').map((l) => l.text());
		expect(labels).toEqual(["All items", "Business laptops"]);
	});

	it("renders the technical characteristics table with Confirmed and Proposed rows", () => {
		const w = make();
		const rows = w.findAll('[data-testid="req-technical-table"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Electrical compatibility");
		expect(rows[0].text()).toContain("Confirmed");
		expect(rows[1].text()).toContain("Memory");
		expect(rows[1].text()).toContain("Proposed");
		expect(rows[1].text()).toContain("Not yet set");
	});

	it("emits confirm-requirement only for a Proposed row, never a Confirmed one", async () => {
		const w = make();
		const rows = w.findAll('[data-testid="req-technical-table"] tbody tr');
		expect(rows[0].find('[data-testid^="req-confirm-"]').exists()).toBe(false);
		await rows[1].find('[data-testid="req-confirm-TECH-002"]').trigger("click");
		expect(w.emitted("confirm-requirement")[0][0].technical_requirement_id).toBe("TECH-002");
	});

	it("filters the table to a named tab's own rows plus every All-items row", async () => {
		const w = make();
		await w.findAll('[role="tablist"] input')[1].setValue(true);
		const rows = w.findAll('[data-testid="req-technical-table"] tbody tr');
		// RQI-001's Proposed Memory row applies; RQI-002 has none of its own,
		// but the All-items Electrical compatibility row still shows.
		expect(rows).toHaveLength(2);
	});

	it("emits add-characteristic when the button is clicked", async () => {
		const w = make();
		await w.find('[data-testid="req-add-characteristic"]').trigger("click");
		expect(w.emitted("add-characteristic")).toBeTruthy();
	});

	it("hydrates the warranty-and-support panel from the package", () => {
		const w = make();
		expect(w.find("#tech-warranty").element.value).toBe("36");
		expect(w.find("#tech-response").element.value).toBe("8");
		expect(w.find("#tech-service-location").element.value).toBe("Within Kenya");
		expect(w.find("#tech-support-desc").element.value).toBe("Supplier to provide escalation and warranty-contact details.");
	});

	it("exposes getPayload with the warranty-and-support fields", async () => {
		const w = make();
		await w.find("#tech-warranty").setValue(24);
		const payload = w.vm.getPayload();
		expect(payload.minimum_warranty_months).toBe(24);
		expect(payload.onsite_support_required).toBe(true);
		expect(payload.support_description).toBe("Supplier to provide escalation and warranty-contact details.");
	});

	it("does not re-hydrate from an in-place refresh carrying the same record_version (AGENTS.md §6.4)", async () => {
		const w = make();
		await w.find("#tech-support-desc").setValue("Typed by the author, not yet saved");
		await w.setProps({ editor: { ...EDITOR } });
		expect(w.find("#tech-support-desc").element.value).toBe("Typed by the author, not yet saved");
	});
});
