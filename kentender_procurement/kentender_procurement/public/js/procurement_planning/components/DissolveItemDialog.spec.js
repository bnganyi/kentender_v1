// PLN-CHG-001 v1.18 §5.6.3/§5.4.6 — DissolveItemDialog component tests (U21-dissolve-item).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DissolveItemDialog from "./DissolveItemDialog.vue";

describe("DissolveItemDialog", () => {
	it("renders the exact frame copy and both actions", () => {
		const wrapper = mount(DissolveItemDialog, { props: { pending: false, error: "" } });
		expect(wrapper.get(".kt-dialog-title").text()).toBe("Dissolve Plan Item?");
		expect(wrapper.text()).toContain(
			"Its eligible sources will return to this Draft's unallocated requirements. This action does not release Budget funds."
		);
		const buttons = wrapper.findAll("button").map((b) => b.text());
		expect(buttons).toEqual(["Cancel", "Dissolve Plan Item"]);
	});

	it("emits cancel and confirm from the respective buttons", async () => {
		const wrapper = mount(DissolveItemDialog, { props: { pending: false, error: "" } });
		await wrapper.get('[data-testid="pln-dissolve-item-confirm"]').trigger("click");
		expect(wrapper.emitted("confirm")).toHaveLength(1);
		await wrapper.findAll("button")[0].trigger("click");
		expect(wrapper.emitted("cancel")).toHaveLength(1);
	});

	it("disables both actions while pending and shows a server error", () => {
		const wrapper = mount(DissolveItemDialog, { props: { pending: true, error: "The item changed." } });
		for (const button of wrapper.findAll("button")) {
			expect(button.attributes("disabled")).toBeDefined();
		}
		expect(wrapper.get('[data-testid="pln-dissolve-item-error"]').text()).toBe("The item changed.");
	});
});
