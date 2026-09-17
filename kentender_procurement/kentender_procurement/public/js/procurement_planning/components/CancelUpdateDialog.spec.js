// PLN-CHG-001 v1.18 §8.2 — CancelUpdateDialog component tests (U21-cancel-update).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CancelUpdateDialog from "./CancelUpdateDialog.vue";

describe("CancelUpdateDialog", () => {
	it("renders the exact frame copy and both actions", () => {
		const wrapper = mount(CancelUpdateDialog, { props: { pending: false, error: "" } });
		expect(wrapper.get(".kt-dialog-title").text()).toBe("Cancel Plan update?");
		expect(wrapper.text()).toContain(
			"The open update will be cancelled. The Active Plan and existing procurement proceedings will remain unchanged."
		);
		const buttons = wrapper.findAll("button").map((b) => b.text());
		expect(buttons).toEqual(["Keep update", "Cancel update"]);
	});

	it("emits cancel from Keep update and confirm from Cancel update", async () => {
		const wrapper = mount(CancelUpdateDialog, { props: { pending: false, error: "" } });
		await wrapper.get('[data-testid="pln-cancel-update-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")).toHaveLength(1);
		await wrapper.findAll("button")[0].trigger("click");
		expect(wrapper.emitted("cancel")).toHaveLength(1);
	});

	it("disables both actions while pending and shows a server error", () => {
		const wrapper = mount(CancelUpdateDialog, { props: { pending: true, error: "Something changed." } });
		for (const button of wrapper.findAll("button")) {
			expect(button.attributes("disabled")).toBeDefined();
		}
		expect(wrapper.get('[data-testid="pln-cancel-update-error"]').text()).toBe("Something changed.");
	});
});
