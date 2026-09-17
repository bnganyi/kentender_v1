// PLN-CHG-001 v1.18 §9.1/§10.2 — WorkspaceScreen component tests (U01-A..G).
// Exact fields, absent fields and action visibility this screen renders,
// straight off the server's `annual_plan.blocks`/`actionable` shape —
// nothing here re-derives a label the server already decided.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const CONTEXT = {
	financial_year: "2027-2028",
	financial_year_label: "FY 2027/28",
	financial_years: [
		{ id: "2027-2028", label: "FY 2027/28" },
		{ id: "2028-2029", label: "FY 2028/29" },
	],
	resolved_financial_year_source: "default",
};

function workspace(overrides = {}) {
	return {
		outcome: "OK",
		context: CONTEXT,
		window_open: true,
		annual_plan: { plan_reference: "PLN-MOH-2027-001", title: "Ministry of Health Annual Procurement Plan", summary: "Annual Plan · Draft Version 1", blocks: [] },
		actionable: [],
		waiting: [],
		schedule_health: null,
		not_included: null,
		departmental_plans: [],
		departmental_plans_heading: "Departmental plans feeding this Annual Plan",
		departmental_plans_lede: "These are the accepted and pending plans behind the entry above.",
		count_label: "0 departmental plans",
		...overrides,
	};
}

function make(props = {}) {
	return mount(WorkspaceScreen, {
		props: { loading: false, error: "", supportRef: "", pending: false, workspace: workspace(), ...props },
	});
}

describe("WorkspaceScreen states", () => {
	it("shows the loading skeleton and nothing else", () => {
		const w = make({ loading: true });
		expect(w.find('[data-testid="pln-loading"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-context-strip"]').exists()).toBe(false);
	});

	it("shows the load error with the support reference and a retry button", () => {
		const w = make({ error: "boom", supportRef: "SR-123" });
		expect(w.find('[data-testid="pln-error"]').text()).toContain("SR-123");
	});

	it("shows the Forbidden panel with no strip, no table", () => {
		const w = make({ workspace: workspace({ outcome: "FORBIDDEN", forbidden: { heading: "You do not have access to Procurement Planning", text: "Ask your KenTender administrator." } }) });
		expect(w.find('[data-testid="pln-forbidden"]').text()).toContain("You do not have access");
		expect(w.find('[data-testid="pln-context-strip"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-departmental-plans"]').exists()).toBe(false);
	});

	it("shows the no-context panel when no Financial Year is available", () => {
		const w = make({ workspace: workspace({ outcome: "NO_CONTEXT" }) });
		expect(w.find('[data-testid="pln-no-context"]').exists()).toBe(true);
	});
});

describe("the Annual Plan card (U01-A..G)", () => {
	it("U01-D: shows No Annual Plan yet when no plan exists", () => {
		const w = make();
		const card = w.find('[data-testid="pln-no-plan"]');
		expect(card.text()).toContain("No Annual Plan yet for FY 2027/28");
		expect(card.text()).toContain("The Draft Annual Plan is created when the first departmental plan is accepted.");
		expect(w.find('[data-testid="pln-annual-plan-card"]').exists()).toBe(false);
	});

	it("U01-A: an initial Draft shows one block with Continue Plan", async () => {
		const w = make({
			workspace: workspace({
				annual_plan: {
					plan_reference: "PLN-MOH-2027-001", summary: "Annual Plan · Draft Version 1",
					blocks: [{ kind: "current", route: ["annual-procurement-plan", "PLN-MOH-2027-001"], version_number: 1, version_status: "Draft", funding_state: "Not requested", plan_items: 2, value_display: "KES 130,000,000", action: "Continue Plan", action_kind: "primary" }],
				},
			}),
		});
		expect(w.find('[data-testid="pln-plan-block-current"]').text()).toContain("KES 130,000,000");
		const button = w.find('[data-testid="pln-plan-action-current"]');
		expect(button.text()).toBe("Continue Plan");
		expect(button.classes()).toContain("kt-btn-primary");
		await button.trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["annual-procurement-plan", "PLN-MOH-2027-001"]);
	});

	it("U01-B: Active plus a Draft successor renders two blocks with distinct actions", () => {
		const w = make({
			workspace: workspace({
				annual_plan: {
					plan_reference: "PLN-MOH-2027-001", summary: "Annual Plan · Active Version 1",
					blocks: [
						{ kind: "active", route: ["annual-procurement-plan", "PLN-MOH-2027-001"], version_number: 1, version_status: "Active", funding_state: "Confirmed", plan_items: 2, value_display: "KES 130,000,000", action: "View Active Plan", action_kind: "secondary" },
						{ kind: "candidate", route: ["annual-procurement-plan", "PLN-MOH-2027-001"], version_number: 2, version_status: "Draft", funding_state: "Confirmed", plan_items: 2, value_display: "KES 130,000,000", action: "Continue update", action_kind: "primary" },
					],
				},
			}),
		});
		expect(w.find('[data-testid="pln-plan-action-active"]').text()).toBe("View Active Plan");
		expect(w.find('[data-testid="pln-plan-action-active"]').classes()).toContain("kt-btn-secondary");
		expect(w.find('[data-testid="pln-plan-action-candidate"]').text()).toBe("Continue update");
		expect(w.find('[data-testid="pln-plan-action-candidate"]').classes()).toContain("kt-btn-primary");
		// U01-B — "Approved value" once cleared statutory approval, "Planned
		// value" for the Draft candidate beside it
		const labels = w.find('[data-testid="pln-annual-plan-card"]').findAll(".kt-label").map((l) => l.text());
		expect(labels).toContain("Approved value");
		expect(labels).toContain("Planned value");
	});

	it.each([
		["Draft", "Planned value"],
		["Awaiting Accounting Officer", "Planned value"],
		["Awaiting statutory approval", "Planned value"],
		["Publication failed", "Planned value"],
		["Active", "Approved value"],
		["Published — activation held", "Approved value"],
	])("U01-A/B/C/F/G — version_status %s uses the %s label", (versionStatus, expectedLabel) => {
		const w = make({
			workspace: workspace({
				annual_plan: {
					plan_reference: "PLN-MOH-2027-001", summary: "",
					blocks: [{ kind: "current", route: ["annual-procurement-plan", "PLN-MOH-2027-001"], version_number: 1, version_status: versionStatus, funding_state: "Confirmed", plan_items: 2, value_display: "KES 130,000,000", action: "", action_kind: "" }],
				},
			}),
		});
		const labels = w.findAll('[data-testid="pln-annual-plan-card"] .kt-label').map((l) => l.text());
		expect(labels).toContain(expectedLabel);
	});

	it("U01-F: a candidate awaiting a decision renders no button on the card itself", () => {
		const w = make({
			workspace: workspace({
				annual_plan: {
					plan_reference: "PLN-MOH-2027-001", summary: "",
					blocks: [{ kind: "current", route: ["annual-procurement-plan", "PLN-MOH-2027-001"], version_number: 1, version_status: "Awaiting Accounting Officer", funding_state: "Confirmed", plan_items: 2, value_display: "KES 130,000,000", action: "", action_kind: "" }],
				},
				actionable: [{ headline: "Review Annual Plan for adoption", supporting: "Version 1 · 2 Plan Items · KES 130,000,000", action: "Open decision", route: ["procurement-planning", "review", "AOT-1"] }],
			}),
		});
		expect(w.find('[data-testid="pln-plan-action-current"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-actionable"]').text()).toContain("Review Annual Plan for adoption");
		expect(w.find('[data-testid="pln-work-action-0"]').text()).toBe("Open decision");
	});
});

describe("actionable rows and departmental plans", () => {
	it("renders one card per actionable row, each with its own headline", () => {
		const w = make({
			workspace: workspace({
				actionable: [
					{ headline: "Validate departmental plan", supporting: "Digital Health · Submission 1", action: "Review", route: ["procurement-planning", "dpp-review", "T1"] },
					{ headline: "Complete Plan readiness", supporting: "Version 1 · Shortfall KES 48,000,000", action: "Review readiness", route: ["annual-procurement-plan", "PLN-MOH-2027-001"] },
				],
			}),
		});
		const cards = w.findAll('[data-testid="pln-actionable"]');
		expect(cards).toHaveLength(2);
		expect(cards[0].text()).toContain("Validate departmental plan");
		expect(cards[1].text()).toContain("Complete Plan readiness");
	});

	// U01-D/E/F — the "Your actions" card shows labelled facts, not one prose
	// line, when the server supplies them.
	it("renders the server's labelled facts instead of the prose supporting line when present", () => {
		const w = make({
			workspace: workspace({
				actionable: [
					{
						headline: "Validate departmental plan",
						supporting: "Digital Health · Submission 1 · 2 requirements · KES 110,000,000 · submitted 25 Nov 2026 by Julia Njeri",
						facts: [
							{ label: "Submitted by", value: "Julia Njeri" },
							{ label: "Submitted", value: "25 Nov 2026, 10:30 EAT" },
							{ label: "Requirements", value: "2" },
							{ label: "Value", value: "KES 110,000,000" },
						],
						action: "Review",
						route: ["procurement-planning", "dpp-review", "T1"],
					},
				],
			}),
		});
		const card = w.find('[data-testid="pln-actionable"]');
		const labels = card.findAll(".kt-label").map((l) => l.text());
		expect(labels).toEqual(["Submitted by", "Submitted", "Requirements", "Value"]);
		expect(card.text()).not.toContain("submitted 25 Nov 2026 by Julia Njeri");
	});

	it("falls back to the prose supporting line when the server sends no facts", () => {
		const w = make({
			workspace: workspace({
				actionable: [{ headline: "Complete Plan readiness", supporting: "Version 1 · Shortfall KES 48,000,000", action: "Review readiness", route: ["annual-procurement-plan", "PLN-MOH-2027-001"] }],
			}),
		});
		const card = w.find('[data-testid="pln-actionable"]');
		expect(card.findAll(".kt-label")).toHaveLength(0);
		expect(card.text()).toContain("Version 1 · Shortfall KES 48,000,000");
	});

	it("emits open-departmental-plan for an Open-departmental-plan route, navigate otherwise", async () => {
		const w = make({
			workspace: workspace({
				actionable: [{ headline: "No departmental plan yet for FY 2027/28", supporting: "Digital Health", action: "Start departmental plan", route: ["procurement-planning", "open", "OU-1"] }],
			}),
		});
		await w.find('[data-testid="pln-work-action-0"]').trigger("click");
		expect(w.emitted("open-departmental-plan")[0]).toEqual(["OU-1"]);
		expect(w.emitted("navigate")).toBeUndefined();
	});

	it("shows the amber not-included notice only when the server names one", () => {
		const w = make({ workspace: workspace({ not_included: { title: "1 accepted Need is not included in any departmental plan", text: "closed before it was added" } }) });
		expect(w.find('[data-testid="pln-not-included"]').text()).toContain("closed before it was added");
	});

	it("renders the departmental plans table and its count label", () => {
		const w = make({
			workspace: workspace({
				departmental_plans: [{ dpp_reference: "DPP-1", department: "Digital Health", version: 1, requirements: 2, value: "KES 110,000,000", status: "Accepted", route: ["departmental-procurement-plan", "DPP-1"] }],
				count_label: "1 departmental plan",
			}),
		});
		expect(w.find('[data-testid="pln-departmental-plans"]').text()).toContain("Digital Health");
		expect(w.find('[data-testid="pln-count-label"]').text()).toBe("1 departmental plan");
	});

	// U01-A/B/C — once any departmental plan has been accepted this FY, the
	// table splits into Accepted/Open Submission with a View action.
	it("uses the Accepted/Open Submission columns with a View action once a plan has been accepted", () => {
		const w = make({
			workspace: workspace({
				departmental_plans_shape: "accepted",
				departmental_plans: [
					{ dpp_reference: "DPP-1", department: "Digital Health", accepted_submission: 1, open_submission: null, requirements: 2, value: "KES 110,000,000", status: "Accepted", route: ["departmental-procurement-plan", "DPP-1"] },
				],
			}),
		});
		const headers = w.findAll('[data-testid="pln-departmental-plans"] th').map((h) => h.text());
		expect(headers).toEqual(["Department", "Accepted Submission", "Open Submission", "Requirements", "Value", "Status", ""]);
		const cells = w.findAll('[data-testid="pln-departmental-plans"] tbody td').map((c) => c.text());
		expect(cells).toEqual(["Digital Health", "1", "None", "2", "KES 110,000,000", "Accepted", "View"]);
	});

	// U01-D — before any acceptance this FY, a single Submission count and no
	// action: there is nothing accepted yet to view.
	it("uses a single Submission column with no action before anything is accepted", () => {
		const w = make({
			workspace: workspace({
				departmental_plans_shape: "submission",
				departmental_plans: [
					{ dpp_reference: "DPP-1", department: "Digital Health", version: 1, requirements: 2, value: "KES 110,000,000", status: "Awaiting validation", route: ["departmental-procurement-plan", "DPP-1"] },
				],
			}),
		});
		const headers = w.findAll('[data-testid="pln-departmental-plans"] th').map((h) => h.text());
		expect(headers).toEqual(["Department", "Submission", "Requirements", "Value", "Status"]);
		expect(w.find('[data-testid="pln-departmental-plans"] button').exists()).toBe(false);
	});
});

describe("the Financial Year filter", () => {
	it("binds to the caller's own selection, not the context echo", () => {
		const w = make({ selectedFinancialYear: "2028-2029" });
		expect(w.find('[data-testid="pln-fy-select"]').element.value).toBe("2028-2029");
	});

	it("falls back to the context's financial_year with no explicit selection", () => {
		const w = make();
		expect(w.find('[data-testid="pln-fy-select"]').element.value).toBe("2027-2028");
	});

	it("emits select-financial-year on change", async () => {
		const w = make();
		await w.find('[data-testid="pln-fy-select"]').setValue("2028-2029");
		expect(w.emitted("select-financial-year")[0]).toEqual(["2028-2029"]);
	});

	it("shows Reset only once a saved default was applied", () => {
		expect(make().find('[data-testid="pln-fy-reset"]').exists()).toBe(false);
		const w = make({ workspace: workspace({ context: { ...CONTEXT, resolved_financial_year_source: "saved_default" } }) });
		expect(w.find('[data-testid="pln-fy-reset"]').exists()).toBe(true);
	});
});
