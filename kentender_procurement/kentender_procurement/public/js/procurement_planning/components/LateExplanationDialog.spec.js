// PLN-CHG-001 v1.23 §10.14 — LateExplanationDialog component tests (U21-LATE-ACTIVATION).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import LateExplanationDialog from "./LateExplanationDialog.vue";

function make(props = {}) {
	return mount(LateExplanationDialog, {
		props: {
			financialYearStarted: "1 Jul 2027",
			activatedAt: "2 Jul 2027, 09:00 EAT",
			pending: false,
			error: "",
			...props,
		},
	});
}

describe("LateExplanationDialog", () => {
	it("§10.14: heads the dialog with the outcome and states only the two read-only facts", () => {
		const wrapper = make();
		expect(wrapper.get(".kt-dialog-title").text()).toBe("Explain late start of the annual plan");
		const facts = wrapper.findAll(".pln-fact-val").map((f) => f.text());
		expect(facts).toEqual(["1 Jul 2027", "2 Jul 2027, 09:00 EAT"]);
		expect(wrapper.get('[data-testid="pln-late-explanation-reason"]').element.value).toBe("");
		// No editable date: this says why the gap exists, it never moves it.
		expect(wrapper.findAll('input[type="date"]')).toHaveLength(0);
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
