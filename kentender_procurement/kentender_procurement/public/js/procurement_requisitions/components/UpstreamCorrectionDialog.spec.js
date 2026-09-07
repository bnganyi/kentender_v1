// §13.13 "Request upstream correction?" dialog.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import UpstreamCorrectionDialog from "./UpstreamCorrectionDialog.vue";

describe("UpstreamCorrectionDialog — §13.13", () => {
	it("pre-fills the exact fixture reason text and the fixed Planning-preservation notice", () => {
		const w = mount(UpstreamCorrectionDialog, { props: { pending: false, error: "" } });
		expect(w.find("#upstream-reason").element.value).toContain("authorised warranty period");
		expect(w.text()).toContain("Requisitions cannot edit an approved Planning fact. This Requisition Version will be preserved.");
	});

	it("rejects a reason under 20 characters", async () => {
		const w = mount(UpstreamCorrectionDialog, { props: { pending: false, error: "" } });
		await w.find("#upstream-reason").setValue("Too short");
		await w.find('[data-testid="req-upstream-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeFalsy();
		expect(w.find(".req-field-error").exists()).toBe(true);
	});

	it("emits confirm with the trimmed reason", async () => {
		const w = mount(UpstreamCorrectionDialog, { props: { pending: false, error: "" } });
		await w.find("#upstream-reason").setValue("  The Budget Line on this Plan Item does not match what was actually approved.  ");
		await w.find('[data-testid="req-upstream-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toBe("The Budget Line on this Plan Item does not match what was actually approved.");
	});

	it("emits cancel", async () => {
		const w = mount(UpstreamCorrectionDialog, { props: { pending: false, error: "" } });
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
