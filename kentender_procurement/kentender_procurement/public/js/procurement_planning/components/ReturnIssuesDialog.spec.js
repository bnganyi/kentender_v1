// PLN-CHG-001 v1.18 §12.6 — ReturnIssuesDialog component tests (U06 overlay,
// "Return departmental plan for correction?"). At least one structured issue
// with its affected entry, the exact fields U06 draws, and Add another issue
// as a legitimate addition beyond the single-issue frame example.
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
	it("renders the frame's exact title, lede and field labels", () => {
		const w = make();
		expect(w.get(".kt-dialog-title").text()).toBe("Return to department?");
		expect(w.text()).toContain("The submitted plan remains unchanged. State each issue and the exact correction required.");
		expect(w.findAll("label").map((l) => l.text())).toEqual(["Affected requirement", "Issue", "Correction required"]);
	});

	it("disables Return to department until every issue row is complete, then emits the issues", async () => {
		const w = make();
		const confirm = w.get('[data-testid="dppv-return-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();

		await w.get('[data-testid="dppv-issue-entry-0"]').setValue("E2");
		await w.get('[data-testid="dppv-issue-problem-0"]').setValue("The indicative amount needs correction.");
		await w.get('[data-testid="dppv-issue-correction-0"]').setValue("Confirm and update the deployment laptop amount.");
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual([
			{ entry_id: "E2", problem: "The indicative amount needs correction.", correction: "Confirm and update the deployment laptop amount." },
		]);
	});

	it("adds another issue row on demand", async () => {
		const w = make();
		expect(w.findAll('[data-testid^="dppv-issue-entry-"]')).toHaveLength(1);
		await w.get('[data-testid="dppv-issue-add"]').trigger("click");
		expect(w.findAll('[data-testid^="dppv-issue-entry-"]')).toHaveLength(2);
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
