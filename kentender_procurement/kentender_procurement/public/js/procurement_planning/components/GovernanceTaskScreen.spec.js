// PLN-CHG-001 v1.2 §15.1(5) — GovernanceTaskScreen component tests (D9).
// PLN-DES-11 (AO adoption) and PLN-DES-12 (statutory approval) exact fields
// from one shared read model, incl. the Board resolution-reference gate.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import GovernanceTaskScreen from "./GovernanceTaskScreen.vue";

const ITEM_ROW = {
	plan_item_id: "PPI-MOH-2027-021",
	title: "National digital health infrastructure upgrade",
	department: "Digital Health",
	source_origin: "Accepted Departmental Need",
	quantity_display: "1 programme",
	strategic_objective_label: "Strengthen interoperable national digital health services",
	procurement_method: "Open Tender",
	value_display: "KES 80,000,000",
	delivery_completion_display: "31 Aug 2027",
	finance_state: "Confirmed",
};

const AO_TASK = {
	task: "AOT-1", task_token: "tok", status: "Open", stage: "Accounting Officer adoption",
	header: {
		eyebrow: "ACCOUNTING OFFICER ADOPTION · PLN-MOH-2027-001 · VERSION 1",
		title: "Ministry of Health Annual Procurement Plan 2027/28", badge: "Awaiting Accounting Officer",
	},
	authority_card: null,
	decision_statement:
		"I adopt the complete consolidated Annual Procurement Plan Version 1 shown above and submit it for the statutory approval applicable to this Procuring Entity.",
	items: [ITEM_ROW],
	caption: "1 Plan Item · KES 80,000,000",
	confirm_label: "Adopt and submit",
	return_dialog: { title: "Return Plan Version for correction?", lede: "lede" },
};

const STATUTORY_TASK = {
	...AO_TASK, stage: "Statutory approval",
	header: { ...AO_TASK.header, eyebrow: "STATUTORY APPROVAL · PLN-MOH-2027-001 · VERSION 1", badge: "Awaiting statutory approval" },
	authority_card: {
		capacity: "Responsible Cabinet Secretary", is_board: false,
		ao_adoption_line: "Amina Hassan · 8 Dec 2026, 10:00 EAT",
	},
	decision_statement: "",
	confirm_label: "Approve Annual Procurement Plan",
};

function make(task = AO_TASK) {
	return mount(GovernanceTaskScreen, { props: { task, pending: false, errorSummary: "" } });
}

describe("GovernanceTaskScreen — PLN-DES-11 AO adoption", () => {
	it("renders the immutable Plan table and the decision statement, no authority card", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toContain("ACCOUNTING OFFICER ADOPTION");
		expect(w.find('[data-testid="pgt-items"]').text()).toContain(
			"National digital health infrastructure upgrade"
		);
		expect(w.text()).toContain("1 Plan Item · KES 80,000,000");
		expect(w.find('[data-testid="pgt-statement"]').text()).toContain("I adopt the complete");
		expect(w.find('[data-testid="pgt-authority"]').exists()).toBe(false);
	});

	it("emits confirm and open-return-dialog", async () => {
		const w = make();
		await w.find('[data-testid="pgt-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toHaveLength(1);
		await w.find('[data-testid="pgt-return"]').trigger("click");
		expect(w.emitted("open-return-dialog")).toHaveLength(1);
	});

	it("carries no editable Plan content, optional comment or publication control", () => {
		const w = make();
		expect(w.findAll("input, textarea, select")).toHaveLength(0);
		expect(w.text()).not.toContain("Comment");
		expect(w.text()).not.toContain("Publish");
	});
});

describe("GovernanceTaskScreen — PLN-DES-12 statutory approval", () => {
	it("renders the authority card with the AO adoption line and no decision statement", () => {
		const w = make(STATUTORY_TASK);
		expect(w.find('[data-testid="pgt-authority"]').text()).toContain("Responsible Cabinet Secretary");
		expect(w.find('[data-testid="pgt-authority"]').text()).toContain("Amina Hassan");
		expect(w.find('[data-testid="pgt-statement"]').exists()).toBe(false);
	});

	it("requires a resolution reference before approving when the capacity is a governing body", async () => {
		const board = {
			...STATUTORY_TASK,
			authority_card: { capacity: "Board of Directors or similar governing body", is_board: true, ao_adoption_line: "x" },
		};
		const w = make(board);
		const confirm = w.find('[data-testid="pgt-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pgt-resolution"]').setValue("BOD-RES-2027-014");
		expect(confirm.attributes("disabled")).toBeUndefined();
	});
});

describe("GovernanceTaskScreen — decided task", () => {
	it("removes the decision footer once the task is no longer Open", () => {
		const w = make({ ...AO_TASK, status: "Completed" });
		expect(w.find('[data-testid="pgt-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="pgt-return"]').exists()).toBe(false);
	});
});
