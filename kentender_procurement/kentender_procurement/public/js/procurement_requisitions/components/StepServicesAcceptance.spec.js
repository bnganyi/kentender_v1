// REQ-DES-06 Step 4: Services and acceptance (§13.8) — the related-services
// info line (table absent, never empty, when No), the acceptance table
// (§5.9's at-least-one-row rule), and the supporting-materials panel.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StepServicesAcceptance from "./StepServicesAcceptance.vue";

const BASE_EDITOR = {
	version: { related_services_required: false },
	package: {
		items: [{ requisition_item_id: "RQI-001", item_name: "Business laptops" }],
		related_services: [],
		acceptance_requirements: [
			{ acceptance_requirement_id: "ACC-001", applies_to_scope: "All items", check_type: "Quantity", pass_condition: "Delivered quantities equal the authorised schedule", evidence_type: "Inspection record" },
		],
		supporting_materials: [],
	},
};

function make(overrides = {}) {
	return mount(StepServicesAcceptance, { props: { editor: { ...BASE_EDITOR, ...overrides } } });
}

describe("StepServicesAcceptance — REQ-DES-06", () => {
	it("shows 'No' and hides the related-services table entirely when not required — never an empty table", () => {
		const w = make();
		expect(w.text()).toContain("Related services required:");
		expect(w.text()).toContain("No");
		expect(w.find('[data-testid="req-services-table"]').exists()).toBe(false);
	});

	it("shows the related-services table with rows when required is Yes", () => {
		const w = make({
			version: { related_services_required: true },
			package: { ...BASE_EDITOR.package, related_services: [{ service_requirement_id: "SVC-001", service_type: "Installation", applies_to_scope: "All items", required_result: "Devices installed and configured", completion_date: "2027-09-30", acceptance_evidence: "Installation certificate" }] },
		});
		const rows = w.findAll('[data-testid="req-services-table"] tbody tr');
		expect(rows).toHaveLength(1);
		expect(rows[0].text()).toContain("Installation");
	});

	it("renders the acceptance table with its rows and an Applies-to label resolved from the item", () => {
		const w = make({
			package: {
				...BASE_EDITOR.package,
				acceptance_requirements: [
					{ acceptance_requirement_id: "ACC-001", applies_to_scope: "Item", applies_to_id: "RQI-001", check_type: "Functional test", pass_condition: "Each device powers on", evidence_type: "Test result" },
				],
			},
		});
		const rows = w.findAll('[data-testid="req-acceptance-table"] tbody tr');
		expect(rows).toHaveLength(1);
		expect(rows[0].text()).toContain("Business laptops");
	});

	it("shows the empty caption, never a bare table, when no supporting materials exist", () => {
		const w = make();
		expect(w.find('[data-testid="req-materials-table"]').exists()).toBe(false);
		expect(w.text()).toContain("No supporting materials added.");
	});

	it("renders the supporting-materials table when rows exist", () => {
		const w = make({
			package: { ...BASE_EDITOR.package, supporting_materials: [{ supporting_material_id: "MAT-001", title: "Site photograph", document_type: "Photograph", treatment: "Informational", file_check_result: "Not scanned — no scanner configured" }] },
		});
		const rows = w.findAll('[data-testid="req-materials-table"] tbody tr');
		expect(rows).toHaveLength(1);
		expect(rows[0].text()).toContain("Site photograph");
	});

	it("emits add-acceptance, add-material and remove events", async () => {
		const w = make();
		await w.find('[data-testid="req-add-acceptance"]').trigger("click");
		expect(w.emitted("add-acceptance")).toBeTruthy();
		await w.find('[data-testid="req-add-material"]').trigger("click");
		expect(w.emitted("add-material")).toBeTruthy();
		await w.find('[data-testid="req-acceptance-table"] .req-quiet-link').trigger("click");
		expect(w.emitted("remove-acceptance")[0][0].acceptance_requirement_id).toBe("ACC-001");
	});
});
