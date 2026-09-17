// PLN-CHG-001 v1.18 §7.2 — LateExplanationDialog component tests (U21-late-explanation).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import LateExplanationDialog from "./LateExplanationDialog.vue";

function make(props = {}) {
	return mount(LateExplanationDialog, {
		props: {
			initialVersion: 1,
			financialYearStarted: "1 Jul 2027",
			activatedAt: "2 Jul 2027, 09:00 EAT",
			pending: false,
			error: "",
			...props,
		},
	});
}

describe("LateExplanationDialog", () => {
	it("renders the three facts and starts with an empty explanation", () => {
		const wrapper = make();
		expect(wrapper.get(".kt-dialog-title").text()).toBe("Record late activation explanation");
		const facts = wrapper.findAll(".pln-fact-val").map((f) => f.text());
		expect(facts).toEqual(["1", "1 Jul 2027", "2 Jul 2027, 09:00 EAT"]);
		expect(wrapper.get('[data-testid="pln-late-explanation-reason"]').element.value).toBe("");
	});

	it("disables Record explanation until text is entered, then emits it trimmed", async () => {
		const wrapper = make();
		const confirm = wrapper.get('[data-testid="pln-late-explanation-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();

		await wrapper.get('[data-testid="pln-late-explanation-reason"]').setValue("  Acknowledgement arrived late.  ");
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		expect(wrapper.emitted("confirm")[0]).toEqual(["Acknowledgement arrived late."]);
	});

	it("emits cancel from the secondary button", async () => {
		const wrapper = make();
		await wrapper.findAll("button")[0].trigger("click");
		expect(wrapper.emitted("cancel")).toHaveLength(1);
	});

	it("disables both actions while pending and shows a server error", () => {
		const wrapper = make({ pending: true, error: "The Version changed." });
		for (const button of wrapper.findAll("button")) {
			expect(button.attributes("disabled")).toBeDefined();
		}
		expect(wrapper.get('[data-testid="pln-late-explanation-error"]').text()).toBe("The Version changed.");
	});
});
