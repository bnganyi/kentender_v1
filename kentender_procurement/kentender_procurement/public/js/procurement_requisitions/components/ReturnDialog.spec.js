// §13.13 "Return Requisition for correction?" dialog.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReturnDialog from "./ReturnDialog.vue";

describe("ReturnDialog — §13.13", () => {
	it("rejects a reason under 20 characters", async () => {
		const w = mount(ReturnDialog, { props: { pending: false, error: "" } });
		await w.find("#return-reason").setValue("Too short");
		await w.find('[data-testid="req-return-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.find(".req-field-error").exists()).toBe(true);
	});

	it("emits confirm with the trimmed reason", async () => {
		const w = mount(ReturnDialog, { props: { pending: false, error: "" } });
		await w.find("#return-reason").setValue("  The processor requirement does not match what the department actually needs.  ");
		await w.find('[data-testid="req-return-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toBe("The processor requirement does not match what the department actually needs.");
	});

	it("emits cancel", async () => {
		const w = mount(ReturnDialog, { props: { pending: false, error: "" } });
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
