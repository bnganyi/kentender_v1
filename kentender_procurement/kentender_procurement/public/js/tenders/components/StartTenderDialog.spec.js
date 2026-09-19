// TPR-DES-02 — supported and unsupported requisition, the six facts, and a
// Start control that is disabled (never hidden) when the actor cannot start.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import StartTenderDialog from "./StartTenderDialog.vue";

const DETAIL = {
	outcome: "OK", handoff: "RQH-1", supported: true, can_start: true, result_text: "Supported — IT equipment using the standard Open Tender format.",
	summary: { purchase: "Clinical training and deployment laptops", requisition_reference: "REQ-MOH-2027-033-001", quantity: "250 Each", approved_value: "KES 50,000,000.00", method: "Open Tender", latest_delivery: "30 Sep 2027" },
	compatibility: [{ check: "Product", expected: "Straightforward off-the-shelf IT equipment", actual: "IT Equipment: Laptop", ok: true }],
	template: { available: true, display_name: "IT Equipment — Open Tender", template_version: "1.1" },
};

describe("StartTenderDialog — TPR-DES-02", () => {
	it("renders the six facts, the Supported notice and both disclosures", async () => {
		const w = mount(StartTenderDialog, { props: { detail: DETAIL, pending: false, error: "" } });
		expect(w.find(".kt-dialog-title").text()).toContain("Start this Tender?");
		expect(w.findAll(".kt-label").map((l) => l.text())).toEqual(["Purchase", "Requisition", "Quantity", "Approved value", "Method", "Latest delivery"]);
		expect(w.find('[data-testid="tnd-start-supported"]').text()).toContain("Supported");
		expect(w.findAll(".kt-disclosure-title").map((t) => t.text())).toEqual(["Why this requisition is supported", "Template and source details"]);
		await w.find(".kt-disclosure-head").trigger("click");
		expect(w.find('[data-testid="tnd-start-checks"]').text()).toContain("Product: IT Equipment: Laptop");
		await w.find('[data-testid="tnd-start-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toHaveLength(1);
	});

	it("disables Start with the unsupported notice and names the failed check", () => {
		const w = mount(StartTenderDialog, { props: { detail: { ...DETAIL, supported: false, can_start: false, result_text: "This requisition is not supported by the current IT-equipment Tender format.", compatibility: [{ check: "Method", expected: "Open Tender", actual: "Restricted Tender", ok: false }] } } });
		expect(w.find('[data-testid="tnd-start-unsupported"]').text()).toContain("not supported");
		expect(w.find('[data-testid="tnd-start-unsupported"]').text()).toContain("Method: Restricted Tender");
		expect(w.find('[data-testid="tnd-start-confirm"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="tnd-start-supported"]').exists()).toBe(false);
	});
});
