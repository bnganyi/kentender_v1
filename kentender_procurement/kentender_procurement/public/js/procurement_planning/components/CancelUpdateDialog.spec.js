// PLN-CHG-001 v1.23 §10.17 U21-CANCEL-UPDATE.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CancelUpdateDialog from "./CancelUpdateDialog.vue";

function make(props = {}) {
	return mount(CancelUpdateDialog, { props: { pending: false, error: "", reason: "", ...props } });
}

describe("CancelUpdateDialog", () => {
	it("reassures that nothing already in force changes", () => {
		const w = make();
		expect(w.text()).toContain("Cancel this plan update?");
		expect(w.text()).toContain("The current plan and existing procurement will remain unchanged.");
		expect(w.text()).toContain("Keep update");
	});

	it("holds the confirm until a real reason is given", async () => {
		const w = make();
		expect(w.get('[data-testid="pln-cancel-update-confirm"]').attributes("disabled")).toBeDefined();

		const short = make({ reason: "changed mind" });
		expect(short.get('[data-testid="pln-cancel-update-confirm"]').attributes("disabled")).toBeDefined();

		const ok = make({ reason: "The department withdrew the additional laptops from this cycle." });
		expect(ok.get('[data-testid="pln-cancel-update-confirm"]').attributes("disabled")).toBeUndefined();
	});

	it("emits confirm and cancel", async () => {
		const w = make({ reason: "The department withdrew the additional laptops from this cycle." });
		await w.get('[data-testid="pln-cancel-update-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toHaveLength(1);
		await w.findAll("button")[0].trigger("click");
		expect(w.emitted("cancel")).toHaveLength(1);
	});

	it("shows a command error without losing the typed reason", () => {
		const w = make({ reason: "The department withdrew the additional laptops from this cycle.", error: "boom" });
		expect(w.get('[data-testid="pln-cancel-update-error"]').text()).toBe("boom");
		expect(w.get('[data-testid="pln-cancel-update-reason"]').element.value).toContain("withdrew");
	});
});
