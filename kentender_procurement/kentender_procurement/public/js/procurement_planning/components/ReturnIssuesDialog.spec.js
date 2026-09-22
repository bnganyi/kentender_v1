// PLN-CHG-001 v1.24 §4.4/§10.5 — ReturnIssuesDialog component tests
// (U06-RETURN). One or more issues, each one required comment against a
// requirement or the whole plan, and Add another issue as a legitimate
// addition beyond the single-issue frame example.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReturnIssuesDialog from "./ReturnIssuesDialog.vue";

const ENTRIES = [
	{ entry_id: "E1", title: "National digital health infrastructure upgrade" },
	{ entry_id: "E2", title: "Clinical deployment laptops for digital health rollout" },
];

function make(props = {}) {
	return mount(ReturnIssuesDialog, { props: { entries: ENTRIES, pending: false, error: "", ...props } });
}

describe("ReturnIssuesDialog", () => {
	it("renders the frame's exact title and field labels, with the plan as an option", () => {
		const w = make();
		expect(w.get(".kt-dialog-title").text()).toBe("What needs to change?");
		expect(w.findAll("label").map((l) => l.text())).toEqual(["Context", "Comment"]);
		const options = w.find('[data-testid="dppv-issue-context-0"]').findAll("option").map((o) => o.text());
		expect(options).toEqual(["Whole departmental plan", ...ENTRIES.map((e) => e.title)]);
	});

	it("disables Return to department until every issue has a comment, then emits entry_id and correction_required only", async () => {
		const w = make();
		const confirm = w.get('[data-testid="dppv-return-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();

		await w.get('[data-testid="dppv-issue-context-0"]').setValue("E2");
		await w.get('[data-testid="dppv-issue-comment-0"]').setValue("Confirm and update the deployment laptop amount.");
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual([
			{ entry_id: "E2", correction_required: "Confirm and update the deployment laptop amount." },
		]);
	});

	it("keeps entry_id null for a whole-plan issue", async () => {
		const w = make();
		await w.get('[data-testid="dppv-issue-context-0"]').setValue("");
		await w.get('[data-testid="dppv-issue-comment-0"]').setValue("The submitted totals do not reconcile.");
		await w.get('[data-testid="dppv-return-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual([
			{ entry_id: null, correction_required: "The submitted totals do not reconcile." },
		]);
	});

	it("adds another issue row on demand", async () => {
		const w = make();
		expect(w.findAll('[data-testid^="dppv-issue-context-"]')).toHaveLength(1);
		await w.get('[data-testid="dppv-issue-add"]').trigger("click");
		expect(w.findAll('[data-testid^="dppv-issue-context-"]')).toHaveLength(2);
	});

	it("disables Cancel and Return to department while pending, and shows a server error", () => {
		const w = make({ pending: true, error: "The submission changed." });
		expect(w.get('[data-testid="dppv-return-confirm"]').attributes("disabled")).toBeDefined();
		const cancel = w.findAll("button").find((b) => b.text() === "Cancel");
		expect(cancel.attributes("disabled")).toBeDefined();
		expect(w.get('[data-testid="dppv-return-error"]').text()).toBe("The submission changed.");
	});

	it("emits cancel from the Cancel button", async () => {
		const w = make();
		const buttons = w.findAll("button").filter((b) => b.text() === "Cancel");
		await buttons[0].trigger("click");
		expect(w.emitted("cancel")).toHaveLength(1);
	});
});
