// PLN-CHG-001 v1.12 §15 — DppValidationScreen + ReturnIssuesDialog tests
// (D14): PLN-DES-06 exact fields, decision gating, dialog copy and completeness.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DppValidationScreen from "./DppValidationScreen.vue";
import ReturnIssuesDialog from "./ReturnIssuesDialog.vue";

const DETAIL = {
	outcome: "OK",
	task: "T1",
	task_token: "tok",
	status: "Open",
	maker_checker_blocked: false,
	header: {
		eyebrow: "DEPARTMENTAL PLAN REVIEW",
		title: "Validate Digital Health departmental plan",
		reference_line: "DPP-MOH-DHI-2027-001 · Submitted Version 1",
		badge: "Awaiting validation",
		badge_kind: "pending",
	},
	context: {
		department: "Digital Health",
		financial_year: "FY 2027/28",
		submitted_by: "Dr Peter Kimani",
		submitted_at: "25 Nov 2026, 10:00 EAT",
		requirements: 2,
		total_display: "KES 100,000,000",
	},
	entries: [
		{
			entry_id: "E1",
			title: "National digital health infrastructure upgrade",
			source_label: "Accepted Need · NDS-MOH-2027-0001",
			quantity_display: "1 programme",
			required_by_display: "31 Aug 2027",
			budget_line_display: "MOH-BL-DHI-2027",
			amount_display: "KES 80,000,000",
			description: "Procure and implement national digital health infrastructure across priority health facilities.",
			expected_operational_result: "Priority health facilities can use secure and interoperable digital health services.",
			not_proceeding: false,
		},
		{
			entry_id: "E2",
			title: "Digital health platform security assessment",
			source_label: "Direct requirement",
			quantity_display: "1 service",
			required_by_display: "31 Oct 2027",
			budget_line_display: "MOH-BL-DHI-2027",
			amount_display: "KES 20,000,000",
		},
	],
	requirement_types: ["Consulting services", "Goods", "Non-consulting services"],
	certification: {
		heading: "Departmental certification",
		text: "I certify that this Departmental Procurement Plan contains the current procurement requirements of Digital Health for FY 2027/28…",
		signed_line: "Certified by Dr Peter Kimani · 25 Nov 2026, 10:00 EAT",
	},
	decided: null,
};

function make(detail = DETAIL, classifications = {}) {
	return mount(DppValidationScreen, {
		props: { detail, classifications, pending: false, errorSummary: "" },
	});
}

describe("DppValidationScreen — PLN-DES-06", () => {
	it("renders the exact submission context card", () => {
		const w = make();
		const context = w.find('[data-testid="dppv-context"]');
		expect(context.text()).toContain("Dr Peter Kimani");
		expect(context.text()).toContain("25 Nov 2026, 10:00 EAT");
		expect(context.text()).toContain("KES 100,000,000");
		expect(w.find(".kt-page-kicker").text()).toBe("DEPARTMENTAL PLAN REVIEW");
		// PLN-DES-06: six facts, no Procuring Entity
		expect(context.findAll("label").map((l) => l.text())).toEqual([
			"Department", "Financial Year", "Submitted by", "Submitted", "Requirements", "Total indicative value",
		]);
		expect(w.text()).not.toContain("Procuring Entity");
		expect(w.findAll("thead th").map((th) => th.text())).toEqual([
			"Requirement", "Source", "Quantity", "Required by", "Procurement Budget Line", "Amount", "Requirement type", "",
		]);
	});

	it("View discloses the submitted narrative read-only without editing anything", async () => {
		const w = make();
		expect(w.find('[data-testid="dppv-detail-E1"]').exists()).toBe(false);
		await w.find('[data-testid="dppv-view-E1"]').trigger("click");
		const detail = w.find('[data-testid="dppv-detail-E1"]');
		expect(detail.text()).toContain("Procure and implement national digital health infrastructure");
		expect(detail.findAll("input, textarea, select")).toHaveLength(0);
	});

	it("a not-proceeding entry needs no classification and shows its status", () => {
		const detail = {
			...DETAIL,
			entries: [DETAIL.entries[0], { ...DETAIL.entries[1], not_proceeding: true, not_proceeding_reason: "Deferred.", amount_display: "—" }],
		};
		const w = make(detail, { E1: "Non-consulting services" });
		expect(w.find('[data-testid="dppv-type-E2"]').exists()).toBe(false);
		expect(w.find('[data-testid="dppv-entry-E2"]').text()).toContain("Not proceeding");
		expect(w.find('[data-testid="dppv-accept"]').attributes("disabled")).toBeUndefined();
	});

	it("gates acceptance on a classification for every entry", async () => {
		const partial = make(DETAIL, { E1: "Non-consulting services" });
		expect(partial.find('[data-testid="dppv-accept"]').attributes("disabled")).toBeDefined();
		const full = make(DETAIL, { E1: "Non-consulting services", E2: "Consulting services" });
		expect(full.find('[data-testid="dppv-accept"]').attributes("disabled")).toBeUndefined();
		await full.find('[data-testid="dppv-accept"]').trigger("click");
		expect(full.emitted("accept")).toHaveLength(1);
	});

	it("shows the certification with the signed line and no editable requirement facts", () => {
		const w = make();
		expect(w.find('[data-testid="dppv-certification"]').text()).toContain(
			"Certified by Dr Peter Kimani · 25 Nov 2026, 10:00 EAT"
		);
		// only the classification selects are editable (§11.7)
		const editables = w.findAll("input, textarea");
		expect(editables).toHaveLength(0);
		expect(w.findAll("select")).toHaveLength(2);
	});

	it("removes the decision footer for the maker-checker-blocked certifier", () => {
		const w = make({ ...DETAIL, maker_checker_blocked: true });
		expect(w.find('[data-testid="dppv-maker-checker"]').text()).toContain(
			"You certified this submission"
		);
		expect(w.find('[data-testid="dppv-accept"]').exists()).toBe(false);
		expect(w.find('[data-testid="dppv-return"]').exists()).toBe(false);
		expect(w.findAll("select")).toHaveLength(0);
	});
});

describe("ReturnIssuesDialog — §12.6", () => {
	function makeDialog() {
		return mount(ReturnIssuesDialog, {
			props: { entries: DETAIL.entries, pending: false, error: "" },
		});
	}

	it("requires entry + problem + correction before confirming", async () => {
		const w = makeDialog();
		const confirm = w.find('[data-testid="dppv-return-confirm"]');
		expect(confirm.attributes("disabled")).toBeDefined();
		await w.find('[data-testid="dppv-issue-problem-0"]').setValue("Amount unsupported");
		expect(confirm.attributes("disabled")).toBeDefined();
		await w
			.find('[data-testid="dppv-issue-correction-0"]')
			.setValue("Align the amount with the budget line.");
		expect(confirm.attributes("disabled")).toBeUndefined();
		await confirm.trigger("click");
		const [issues] = w.emitted("confirm")[0];
		expect(issues[0]).toEqual({
			entry_id: "E1",
			problem: "Amount unsupported",
			correction: "Align the amount with the budget line.",
		});
	});

	it("carries no reason category, attachment, assignee or due date (§11.17)", () => {
		const w = makeDialog();
		expect(w.text()).not.toContain("Category");
		expect(w.text()).not.toContain("Attachment");
		expect(w.text()).not.toContain("Assignee");
		expect(w.text()).not.toContain("Due date");
		expect(w.find('input[type="file"]').exists()).toBe(false);
	});
});
