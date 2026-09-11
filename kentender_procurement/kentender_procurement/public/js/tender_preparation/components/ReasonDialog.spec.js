// §13.9 reason dialogs — one required reason (10–1,000), Cancel + named action.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReasonDialog from "./ReasonDialog.vue";

const props = { title: "Return for correction", fieldLabel: "Correction required", confirmLabel: "Return for correction", testid: "tpr-return-dialog" };

describe("ReasonDialog — §13.9", () => {
	it("renders the title, the field label, Cancel and the named primary action", () => {
		const w = mount(ReasonDialog, { props });
		expect(w.find(".kt-dialog-title").text()).toBe("Return for correction");
		expect(w.find("label").text()).toBe("Correction required");
		expect(w.findAll("button").map((b) => b.text())).toEqual(["Cancel", "Return for correction"]);
		expect(w.attributes("data-testid")).toBe("tpr-return-dialog");
	});

	it("refuses a reason under 10 characters inline and emits the trimmed reason otherwise", async () => {
		const w = mount(ReasonDialog, { props });
		await w.find("textarea").setValue("short");
		await w.find('[data-testid="tpr-return-dialog-confirm"]').trigger("click");
		expect(w.find(".tpr-field-error").text()).toBe("A reason of 10–1,000 characters is required.");
		expect(w.emitted("confirm")).toBeFalsy();
		await w.find("textarea").setValue("  Confirm the manufacturer authorisation requirement.  ");
		await w.find('[data-testid="tpr-return-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0]).toEqual(["Confirm the manufacturer authorisation requirement."]);
	});

	it("shows the fixed notice and the server error inline, and emits cancel", async () => {
		const w = mount(ReasonDialog, { props: { ...props, notice: "This Tender Version will be preserved.", error: "The Tender changed since you opened it." } });
		expect(w.text()).toContain("This Tender Version will be preserved.");
		expect(w.find("[role='alert']").text()).toBe("The Tender changed since you opened it.");
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
