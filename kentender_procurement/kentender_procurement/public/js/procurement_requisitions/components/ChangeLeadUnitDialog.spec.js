// REQ-DES-09's "Change lead department?" dialog (§13.11/§5.1).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ChangeLeadUnitDialog from "./ChangeLeadUnitDialog.vue";

const TASK = {
	requisition: { lead_org_unit: "OU-DHI" },
	contributing_org_unit_labels: { "OU-DHI": "Digital Health", "OU-HRMD": "Human Resources Management and Development" },
};

function make() {
	return mount(ChangeLeadUnitDialog, { props: { task: TASK, pending: false, error: "" } });
}

describe("ChangeLeadUnitDialog — REQ-DES-09/§5.1", () => {
	it("offers only the Plan Item's contributing departments, pre-selecting the current lead", () => {
		const w = make();
		const options = w.find("#lead-unit-select").findAll("option").map((o) => o.text());
		expect(options).toEqual(["Digital Health", "Human Resources Management and Development"]);
		expect(w.find("#lead-unit-select").element.value).toBe("OU-DHI");
	});

	it("rejects a reason under 20 characters", async () => {
		const w = make();
		await w.find("#lead-unit-reason").setValue("Too short");
		await w.find('[data-testid="req-change-lead-unit-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.find(".req-field-error").exists()).toBe(true);
	});

	it("emits confirm with the selected unit and trimmed reason", async () => {
		const w = make();
		await w.find("#lead-unit-select").setValue("OU-HRMD");
		await w.find("#lead-unit-reason").setValue("HRMD holds the larger share of this requirement and should certify it.");
		await w.find('[data-testid="req-change-lead-unit-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual({ new_lead_org_unit: "OU-HRMD", reason: "HRMD holds the larger share of this requirement and should certify it." });
	});

	it("emits cancel", async () => {
		const w = make();
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
