// PLN-CHG-001 v1.2 §15.1(5) — FinanceReturnDialog component tests (D9).
// §12.9 requires one actionable reason and no reservation; §11.17's
// absences (no category/attachment/assignee/due date) apply to this dialog
// too, even though no artboard names it explicitly.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FinanceReturnDialog from "./FinanceReturnDialog.vue";

function make() {
	return mount(FinanceReturnDialog, { props: { pending: false, error: "" } });
}

describe("FinanceReturnDialog — §12.9", () => {
	it("requires a reason of at least 10 characters before confirming", async () => {
		const w = make();
		const confirm = w.find('[data-testid="fnt-return-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="fnt-return-reason"]').setValue("too short");
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="fnt-return-reason"]').setValue(
			"The indicative amount exceeds the approved Budget Line ceiling."
		);
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		expect(w.emitted("confirm")[0]).toEqual([
			"The indicative amount exceeds the approved Budget Line ceiling.",
		]);
	});

	it("carries no reason category, attachment, assignee, due date or optional note (§11.17)", () => {
		const w = make();
		expect(w.text()).not.toContain("Category");
		expect(w.text()).not.toContain("Attachment");
		expect(w.text()).not.toContain("Assignee");
		expect(w.text()).not.toContain("Due date");
		expect(w.find('input[type="file"]').exists()).toBe(false);
		expect(w.findAll("textarea")).toHaveLength(1);
	});
});
