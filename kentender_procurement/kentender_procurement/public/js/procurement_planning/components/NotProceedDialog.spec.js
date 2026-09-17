// PLN-CHG-001 v1.18 §5.1.4 — NotProceedDialog component tests (U03 overlay).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import NotProceedDialog from "./NotProceedDialog.vue";

describe("NotProceedDialog", () => {
	it("renders the exact frame copy and starts with an empty reason", () => {
		const wrapper = mount(NotProceedDialog, { props: { pending: false, error: "" } });
		expect(wrapper.get(".kt-dialog-title").text()).toBe("Do not proceed this financial year?");
		expect(wrapper.get('[data-testid="pln-not-proceed-reason"]').element.value).toBe("");
	});

	it("disables Do not proceed under the 20-character minimum, then emits it trimmed", async () => {
		const wrapper = mount(NotProceedDialog, { props: { pending: false, error: "" } });
		const confirm = wrapper.get('[data-testid="pln-not-proceed-confirm"]');
		await wrapper.get('[data-testid="pln-not-proceed-reason"]').setValue("too short");
		expect(confirm.attributes("disabled")).toBeDefined();

		await wrapper.get('[data-testid="pln-not-proceed-reason"]').setValue("  The department will pursue this requirement later.  ");
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		expect(wrapper.emitted("confirm")[0]).toEqual(["The department will pursue this requirement later."]);
	});

	it("emits cancel from the secondary button", async () => {
		const wrapper = mount(NotProceedDialog, { props: { pending: false, error: "" } });
		await wrapper.findAll("button")[0].trigger("click");
		expect(wrapper.emitted("cancel")).toHaveLength(1);
	});

	it("disables both actions while pending and shows a server error", () => {
		const wrapper = mount(NotProceedDialog, { props: { pending: true, error: "The entry changed." } });
		for (const button of wrapper.findAll("button")) {
			expect(button.attributes("disabled")).toBeDefined();
		}
		expect(wrapper.get('[data-testid="pln-not-proceed-error"]').text()).toBe("The entry changed.");
	});
});
