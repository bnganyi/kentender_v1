// PLN-CHG-001 v1.2 §15.1(5) — DppPlanScreen component tests (D9): PLN-DES-02
// and PLN-DES-05 exact fields, absent fields, dialog copy, action visibility.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DppPlanScreen from "./DppPlanScreen.vue";

const DRAFT_PLAN = {
	outcome: "OK",
	access: "author",
	mutable: true,
	can_submit: false,
	header: {
		title: "Digital Health departmental plan",
		reference_line: "DPP-MOH-DHI-2027-001 · Version 1",
		badge: "Draft",
		badge_kind: "attention",
	},
	context: {
		procuring_entity: "PE-MOH — Ministry of Health",
		department: "OU-MOH-DHI — Digital Health",
		financial_year: "FY 2027/28",
		window: { state: "Open", display: "Open until 30 Nov 2026, 23:59 EAT" },
	},
	readiness: {
		title: "1 requirement needs funding details",
		text: "Select a Budget Line and enter the indicative amount for every requirement before the plan can be submitted.",
	},
	entries: [
		{
			entry_id: "E1",
			source_origin: "Accepted Departmental Need",
			title: "National digital health infrastructure upgrade",
			source_label: "Accepted Need · NDS-MOH-2027-0001",
			quantity_display: "1 programme",
			required_by_display: "31 Aug 2027",
			budget_line_display: "Not selected",
			amount_display: "—",
			status: "Funding incomplete",
			status_kind: "attention",
			action: "Complete",
			issues: [],
		},
		{
			entry_id: "E2",
			source_origin: "Direct departmental requirement",
			title: "Digital health platform security assessment",
			source_label: "Direct requirement",
			quantity_display: "1 service",
			required_by_display: "31 Oct 2027",
			budget_line_display: "MOH-BL-DHI-2027",
			amount_display: "KES 20,000,000",
			status: "Ready",
			status_kind: "live",
			action: "Edit",
			issues: [],
		},
	],
	totals_caption: "2 requirements · KES 20,000,000 specified",
	certification: { show: false, heading: "", text: "", checkbox_label: "" },
};

const READY_PLAN = {
	...DRAFT_PLAN,
	access: "hod",
	can_submit: true,
	readiness: null,
	header: { ...DRAFT_PLAN.header, badge: "Ready to submit", badge_kind: "live" },
	entries: DRAFT_PLAN.entries.map((row) => ({
		...row,
		status: "Ready",
		status_kind: "live",
		action: "View",
		budget_line_display: "MOH-BL-DHI-2027",
	})),
	totals_caption: "2 requirements · KES 100,000,000",
	certification: {
		show: true,
		heading: "Departmental certification",
		text: "I certify that this Departmental Procurement Plan contains the current procurement requirements of Digital Health for FY 2027/28, including every current accepted Departmental Need and any direct departmental requirements shown. I confirm that the quantities, required-by dates, Budget Lines and indicative amounts are ready for Procurement validation and inclusion in the Annual Procurement Plan.",
		checkbox_label: "I confirm this certification",
	},
};

function make(plan, extra = {}) {
	return mount(DppPlanScreen, {
		props: { plan, pending: false, certified: false, errorSummary: "", ...extra },
	});
}

describe("DppPlanScreen — PLN-DES-02", () => {
	it("renders header, badge, context strip and the amber readiness notice", () => {
		const w = make(DRAFT_PLAN);
		expect(w.find(".kt-page-kicker").text()).toBe("DEPARTMENTAL PROCUREMENT PLAN");
		expect(w.find(".kt-page-title").text()).toBe("Digital Health departmental plan");
		expect(w.find(".pln-quiet-ref").text()).toBe("DPP-MOH-DHI-2027-001 · Version 1");
		expect(w.find('[data-testid="dpp-badge"]').text()).toBe("Draft");
		expect(w.find('[data-testid="dpp-context"]').text()).toContain(
			"Open until 30 Nov 2026, 23:59 EAT"
		);
		const notice = w.find('[data-testid="dpp-readiness"]');
		expect(notice.text()).toContain("1 requirement needs funding details");
		expect(notice.text()).toContain("Select a Budget Line and enter the indicative amount");
	});

	it("renders the exact table rows with Complete/Edit actions and the caption", () => {
		const w = make(DRAFT_PLAN);
		const rows = w.findAll('[data-testid="dpp-entries"] tbody tr');
		expect(rows[0].text()).toContain("Accepted Need · NDS-MOH-2027-0001");
		expect(rows[0].text()).toContain("Not selected");
		expect(rows[0].find("button").text()).toBe("Complete");
		expect(rows[1].find("button").text()).toBe("Edit");
		expect(w.find('[data-testid="dpp-totals"]').text()).toBe(
			"2 requirements · KES 20,000,000 specified"
		);
	});

	it("disables submit while incomplete and shows no certification card", () => {
		const w = make(DRAFT_PLAN);
		expect(w.find('[data-testid="dpp-submit"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="dpp-certification"]').exists()).toBe(false);
	});

	it("shows no Strategy, requirement-type or currency-selector columns (§11.3)", () => {
		const w = make(DRAFT_PLAN);
		const headers = w.findAll("thead th").map((th) => th.text());
		expect(headers).toEqual([
			"Requirement", "Source", "Quantity", "Required by", "Budget Line",
			"Indicative amount", "Status", "",
		]);
	});

	it("renders returned issues next to their entry (§12.2)", () => {
		const plan = {
			...DRAFT_PLAN,
			entries: [
				{
					...DRAFT_PLAN.entries[1],
					issues: [{ problem: "Amount unsupported", correction: "Align with the budget line." }],
				},
			],
		};
		const w = make(plan);
		const issue = w.find('[data-testid="dpp-issue"]');
		expect(issue.text()).toContain("Amount unsupported");
		expect(issue.text()).toContain("Align with the budget line.");
	});
});

describe("DppPlanScreen — PLN-DES-05", () => {
	it("renders the exact certification text with the checkbox gating submit", async () => {
		const w = make(READY_PLAN);
		const cert = w.find('[data-testid="dpp-certification"]');
		expect(cert.text()).toContain("Departmental certification");
		expect(cert.text()).toContain(
			"including every current accepted Departmental Need and any direct departmental requirements shown"
		);
		expect(w.find('[data-testid="dpp-submit"]').attributes("disabled")).toBeDefined();
		await cert.find('input[type="checkbox"]').setValue(true);
		expect(w.emitted("update:certified")[0][0]).toBe(true);
		const armed = make(READY_PLAN, { certified: true });
		expect(armed.find('[data-testid="dpp-submit"]').attributes("disabled")).toBeUndefined();
	});

	it("ready rows read View and the totals drop the 'specified' suffix", () => {
		const w = make(READY_PLAN);
		expect(w.findAll('[data-testid="dpp-entries"] tbody tr button').map((b) => b.text()))
			.toEqual(["View", "View"]);
		expect(w.find('[data-testid="dpp-totals"]').text()).toBe(
			"2 requirements · KES 100,000,000"
		);
	});

	it("a non-mutable plan offers no editing affordances at all", () => {
		const submitted = {
			...READY_PLAN,
			mutable: false,
			can_submit: false,
			certification: { ...READY_PLAN.certification, show: false },
			entries: READY_PLAN.entries.map((row) => ({ ...row, action: "" })),
			header: { ...READY_PLAN.header, badge: "Awaiting validation", badge_kind: "attention" },
		};
		const w = make(submitted);
		expect(w.find('[data-testid="dpp-add-direct"]').exists()).toBe(false);
		expect(w.find('[data-testid="dpp-submit"]').exists()).toBe(false);
		expect(w.findAll('[data-testid="dpp-entries"] tbody tr button')).toHaveLength(0);
	});
});
