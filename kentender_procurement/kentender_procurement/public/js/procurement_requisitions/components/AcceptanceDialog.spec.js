// REQ-DES-06's "Add acceptance check" dialog (§5.9) — including the
// client-side hint that "Satisfactory"/"acceptable" alone, with no
// observable condition, is rejected (the server's own finding is the real
// gate; this only catches the common case before a round trip).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AcceptanceDialog from "./AcceptanceDialog.vue";

const EDITOR = {
	package: {
		items: [{ requisition_item_id: "RQI-001", item_name: "Business laptops", plan_item_line_id: "DL-001" }],
		related_services: [{ service_requirement_id: "SVC-001", service_type: "Installation" }],
	},
	catalogue: {
		acceptance_check_types: ["Quantity", "Functional test"],
		acceptance_evidence_types: ["Inspection record", "Test result", "Other stated record"],
	},
};

function make() {
	return mount(AcceptanceDialog, { props: { editor: EDITOR, pending: false, error: "" } });
}

describe("AcceptanceDialog — REQ-DES-06", () => {
	it("rejects 'Satisfactory' alone as a pass condition", async () => {
		const w = make();
		await w.find("#acc-check-type").setValue("Functional test");
		await w.find("#acc-pass-condition").setValue("Satisfactory");
		await w.find("#acc-evidence").setValue("Test result");
		await w.find('[data-testid="req-acceptance-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.find(".req-field-error").text()).toContain("observable condition");
	});

	it("accepts an observable pass condition that happens to contain 'acceptable'", async () => {
		const w = make();
		await w.find("#acc-check-type").setValue("Functional test");
		await w.find("#acc-pass-condition").setValue("Each device powers on within an acceptable 30-second window and completes the basic test.");
		await w.find("#acc-evidence").setValue("Test result");
		await w.find('[data-testid="req-acceptance-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeTruthy();
	});

	it("submits Service scope and id when a service row is chosen as Applies to", async () => {
		const w = make();
		await w.find("#acc-applies-to").setValue("SVC-001");
		await w.find("#acc-check-type").setValue("Quantity");
		await w.find("#acc-pass-condition").setValue("Delivered quantities equal the authorised schedule for this service.");
		await w.find("#acc-evidence").setValue("Inspection record");
		await w.find('[data-testid="req-acceptance-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.applies_to_scope).toBe("Service");
		expect(payload.applies_to_id).toBe("SVC-001");
	});

	it("requires other_evidence_name only when evidence is Other stated record", async () => {
		const w = make();
		await w.find("#acc-check-type").setValue("Quantity");
		await w.find("#acc-pass-condition").setValue("Delivered quantities equal the authorised schedule exactly.");
		await w.find("#acc-evidence").setValue("Other stated record");
		await w.find('[data-testid="req-acceptance-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		await w.find("#acc-other-evidence").setValue("Signed acceptance form");
		await w.find('[data-testid="req-acceptance-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeTruthy();
	});
});
