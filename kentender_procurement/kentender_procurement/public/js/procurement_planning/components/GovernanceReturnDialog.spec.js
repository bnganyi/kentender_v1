// PLN-CHG-001 v1.2 §15.1(5) — GovernanceReturnDialog component tests (D9).
// PLN-DES-15's two exact dialog copies, driven by the read model, and the
// required-reason gate.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import GovernanceReturnDialog from "./GovernanceReturnDialog.vue";

function make(dialog) {
	return mount(GovernanceReturnDialog, { props: { dialog, pending: false, error: "" } });
}

describe("GovernanceReturnDialog — PLN-DES-15", () => {
	it("renders the Accounting Officer stage's exact title and intro", () => {
		const w = make({
			title: "Return Plan Version for correction?",
			lede: "The submitted Version 1 remains unchanged. State the correction required.",
		});
		expect(w.find(".kt-dialog-title").text()).toBe("Return Plan Version for correction?");
		expect(w.text()).toContain("The submitted Version 1 remains unchanged.");
	});

	it("renders the statutory stage's exact title and intro", () => {
		const w = make({
			title: "Return adopted Plan Version for correction?",
			lede: "The Accounting-Officer-adopted Version 1 remains unchanged. State the correction required.",
		});
		expect(w.find(".kt-dialog-title").text()).toBe("Return adopted Plan Version for correction?");
	});

	it("requires a reason of at least 10 characters before confirming", async () => {
		const w = make({ title: "t", lede: "l" });
		const confirm = w.find('[data-testid="pgt-return-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pgt-return-reason"]').setValue(
			"Confirm the planned contract-signing date against the delivery completion date."
		);
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([
			"Confirm the planned contract-signing date against the delivery completion date.",
		]);
	});

	it("carries no reason category, attachment, assignee or due date (§11.17)", () => {
		const w = make({ title: "t", lede: "l" });
		expect(w.text()).not.toContain("Category");
		expect(w.text()).not.toContain("Attachment");
		expect(w.find('input[type="file"]').exists()).toBe(false);
	});
});
