// REQ-DES-06's "Add related service" dialog (§5.8).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ServiceDialog from "./ServiceDialog.vue";

const EDITOR = {
	package: { items: [{ requisition_item_id: "RQI-001", item_name: "Business laptops", plan_item_line_id: "DL-001" }] },
	catalogue: {
		service_types: ["Delivery", "Installation"],
		service_acceptance_evidence: ["Delivery note", "Installation certificate", "Other stated record"],
	},
};

function make() {
	return mount(ServiceDialog, { props: { editor: EDITOR, pending: false, error: "" } });
}

async function fillValid(w, { evidence = "Delivery note" } = {}) {
	await w.find("#svc-type").setValue("Installation");
	await w.find("#svc-result").setValue("Devices installed and configured at the delivery location.");
	await w.find("#svc-coverage").setValue("2 units");
	await w.find("#svc-date").setValue("2027-09-30");
	await w.find("#svc-evidence").setValue(evidence);
	if (evidence === "Other stated record") await w.find("#svc-other-evidence").setValue("Signed handover note");
}

describe("ServiceDialog — REQ-DES-06", () => {
	it("rejects an incomplete submission with field-level errors", async () => {
		const w = make();
		await w.find('[data-testid="req-service-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.findAll(".req-field-error").length).toBeGreaterThan(0);
	});

	it("submits All-items scope by default", async () => {
		const w = make();
		await fillValid(w);
		await w.find('[data-testid="req-service-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.applies_to_scope).toBe("All items");
		expect(payload.service_type).toBe("Installation");
	});

	it("submits Item scope when a specific item is chosen", async () => {
		const w = make();
		await w.find("#svc-applies-to").setValue("RQI-001");
		await fillValid(w);
		await w.find('[data-testid="req-service-dialog-confirm"]').trigger("click");
		const payload = w.emitted("confirm")[0][0];
		expect(payload.applies_to_scope).toBe("Item");
		expect(payload.applies_to_id).toBe("RQI-001");
	});

	it("requires other_evidence_name only when evidence is Other stated record", async () => {
		const w = make();
		await fillValid(w, { evidence: "Other stated record" });
		await w.find('[data-testid="req-service-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0].other_evidence_name).toBe("Signed handover note");
	});

	it("emits cancel", async () => {
		const w = make();
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
