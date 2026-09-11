// §13.13 "Revoke unconsumed authorisation?" dialog.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import RevokeDialog from "./RevokeDialog.vue";

describe("RevokeDialog — §13.13", () => {
	it("renders the fixed reversal notice", () => {
		const w = mount(RevokeDialog, { props: { pending: false, error: "" } });
		expect(w.find(".kt-dialog-title").text()).toBe("Revoke unconsumed authorisation?");
		expect(w.text()).toContain("The Planning drawdown and both Budget reservations will be reversed. The authorised Version remains in history.");
	});

	it("rejects a reason under 20 characters", async () => {
		const w = mount(RevokeDialog, { props: { pending: false, error: "" } });
		await w.find("#revoke-reason").setValue("Too short");
		await w.find('[data-testid="req-revoke-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.find(".req-field-error").exists()).toBe(true);
	});

	it("emits confirm with the trimmed reason", async () => {
		const w = mount(RevokeDialog, { props: { pending: false, error: "" } });
		await w.find("#revoke-reason").setValue("  The Plan Item's delivery date changed after authorisation and this must be re-drawn.  ");
		await w.find('[data-testid="req-revoke-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toBe("The Plan Item's delivery date changed after authorisation and this must be re-drawn.");
	});

	it("emits cancel", async () => {
		const w = mount(RevokeDialog, { props: { pending: false, error: "" } });
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
