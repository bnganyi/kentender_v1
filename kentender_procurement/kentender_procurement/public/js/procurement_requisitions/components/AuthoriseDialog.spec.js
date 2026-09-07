// §13.13 "Authorise Requisition?" dialog.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AuthoriseDialog from "./AuthoriseDialog.vue";

const TASK = {
	version: {
		drawdown_lines: [
			{ drawdown_line_id: "DL-001", requested_quantity: 100, requested_value: 20_000_000, unit: "Each" },
			{ drawdown_line_id: "DL-002", requested_quantity: 150, requested_value: 30_000_000, unit: "Each" },
		],
	},
	budget_affordability: [{ budget_line: "vt678eghgt", budget_line_label: "MOH-BL-HWD-2027", requested_amount: 50_000_000 }],
};

describe("AuthoriseDialog — §13.13", () => {
	it("renders the exact total quantity/value and the named Budget line commitment notice", () => {
		const w = mount(AuthoriseDialog, { props: { task: TASK, pending: false, error: "" } });
		expect(w.find(".kt-dialog-title").text()).toBe("Authorise Requisition?");
		expect(w.text()).toContain("250 Each · KES 50,000,000.00");
		expect(w.text()).toContain("reserves the requested value against MOH-BL-HWD-2027");
		expect(w.text()).toContain("creates the immutable Tender Preparation handoff");
	});

	it("emits confirm and cancel", async () => {
		const w = mount(AuthoriseDialog, { props: { task: TASK, pending: false, error: "" } });
		await w.find('[data-testid="req-authorise-dialog-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeTruthy();
		await w.find(".kt-btn-secondary").trigger("click");
		expect(w.emitted("cancel")).toBeTruthy();
	});
});
