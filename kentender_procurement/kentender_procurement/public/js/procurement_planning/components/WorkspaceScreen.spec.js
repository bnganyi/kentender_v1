// PLN-CHG-001 v1.12 §15 — WorkspaceScreen component tests (D14). Exact
// fields, absent fields, copy and action visibility for PLN-DES-01 and the
// PLN-DES-16 states this screen renders.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const CONTEXT = {
	financial_year: "2027-2028",
	financial_years: [
		{ id: "2027-2028", label: "FY 2027/28" },
		{ id: "2028-2029", label: "FY 2028/29" },
	],
	resolved_financial_year_source: "default",
};

const WORKSPACE = {
	outcome: "OK",
	context: CONTEXT,
	window_open: true,
	annual_plan: { plan_reference: "PLN-MOH-2027", summary: "Annual Plan · Draft Version 1" },
	actionable: [
		{
			headline: "1 accepted departmental entry ready to consolidate",
			supporting: "Digital Health · KES 80,000,000",
			action: "Open Annual Plan",
			route: ["annual-procurement-plan", "PLN-MOH-2027"],
			kind: "live",
		},
	],
	waiting: [],
	schedule_health: null,
	departmental_plans: [
		{
			dpp_reference: "DPP-MOH-DHI-2027-001",
			department: "Digital Health",
			version: 1,
			requirements: 1,
			value: "KES 80,000,000",
			status: "Accepted",
			status_kind: "live",
			route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"],
		},
		{
			dpp_reference: "DPP-MOH-HRMD-2027-001",
			department: "Human Resources Management and Development",
			version: 1,
			requirements: 2,
			value: "KES 88,000,000",
			status: "Not submitted — window closed",
			status_kind: "critical",
			route: ["departmental-procurement-plan", "DPP-MOH-HRMD-2027-001"],
		},
	],
	departmental_plans_heading: "Departmental plans feeding this Annual Plan",
	departmental_plans_lede: "These are the accepted and pending plans behind the entry above.",
	count_label: "2 departmental plans",
	not_included: {
		title: "2 accepted Needs are not included in any departmental plan",
		text: "2 accepted Needs from Human Resources Management and Development were not included because the departmental-plan submission window closed before they were added. Ask the department to raise this with your KenTender administrator.",
	},
};

function make(overrides = {}) {
	return mount(WorkspaceScreen, {
		props: {
			loading: false,
			error: "",
			supportRef: "",
			workspace: WORKSPACE,
			pending: false,
			...overrides,
		},
	});
}

describe("WorkspaceScreen — PLN-DES-01", () => {
	it("renders the exact masthead copy with no header action button", () => {
		const w = make();
		expect(w.find(".kt-page-kicker").text()).toBe("PROCUREMENT PLANNING");
		expect(w.find(".kt-page-title").text()).toBe("Annual procurement planning");
		expect(w.find(".kt-page-lede").text()).toContain(
			"Turn accepted departmental plans into a funded and approved Annual Procurement Plan."
		);
		expect(w.find(".pln-masthead button").exists()).toBe(false);
	});

	it("renders the Financial Year as a plain inline filter, never a card, with no Procuring Entity control", () => {
		const w = make();
		const strip = w.find('[data-testid="pln-context-strip"]');
		expect(strip.classes()).not.toContain("kt-card");
		expect(strip.find("label").text()).toBe("Financial Year");
		const select = w.find('[data-testid="pln-fy-select"]');
		expect(select.element.tagName).toBe("SELECT");
		expect(select.findAll("option").map((o) => o.text())).toEqual(["FY 2027/28", "FY 2028/29"]);
		expect(w.find('[data-testid="pln-plan-summary"]').text()).toBe("· Annual Plan · Draft Version 1");
		expect(w.text()).not.toContain("Procuring Entity");
		expect(w.find('[data-testid="pln-pe-select"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-fy-reset"]').exists()).toBe(false);
	});

	it("emits the selected year and shows the reset only for a remembered selection", async () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				context: { ...CONTEXT, resolved_financial_year_source: "saved_default" },
			},
		});
		await w.find('[data-testid="pln-fy-select"]').setValue("2028-2029");
		expect(w.emitted("select-financial-year")[0][0]).toBe("2028-2029");
		await w.find('[data-testid="pln-fy-reset"]').trigger("click");
		expect(w.emitted("reset-financial-year")).toHaveLength(1);
	});

	it("renders the actionable card as headline-plus-button rows, titled Ready to consolidate", async () => {
		const w = make();
		const card = w.find('[data-testid="pln-actionable"]');
		expect(card.find(".kt-card-title").text()).toBe("Ready to consolidate");
		expect(card.find("table").exists()).toBe(false);
		expect(card.find("th").exists()).toBe(false);
		const row = card.find('[data-testid="pln-action-row"]');
		expect(row.find(".pln-ready-headline").text()).toBe(
			"1 accepted departmental entry ready to consolidate"
		);
		expect(row.find(".pln-ready-sub").text()).toBe("Digital Health · KES 80,000,000");
		expect(row.find("button").classes()).toContain("kt-btn-primary");
		await row.find("button").trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["annual-procurement-plan", "PLN-MOH-2027"]);
	});

	it("titles mixed work as Your work and keeps every row in one card", () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				actionable: [
					...WORKSPACE.actionable,
					{ headline: "Validate departmental plan", supporting: "Digital Health", action: "Review", route: ["procurement-planning", "dpp-review", "T1"], kind: "attention" },
				],
			},
		});
		const card = w.find('[data-testid="pln-actionable"]');
		expect(card.find(".kt-card-title").text()).toBe("Your work");
		expect(w.findAll('[data-testid="pln-action-row"]')).toHaveLength(2);
		expect(w.findAll('[data-testid="pln-actionable"]')).toHaveLength(1);
	});

	it("omits the actionable card entirely when nothing is actionable", () => {
		const w = make({ workspace: { ...WORKSPACE, actionable: [] } });
		expect(w.find('[data-testid="pln-actionable"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Your work");
	});

	it("renders the amber not-included notice with the exact copy", () => {
		const w = make();
		const notice = w.find('[data-testid="pln-not-included"]');
		expect(notice.classes()).toContain("pln-notice");
		expect(notice.find(".pln-notice-title").text()).toBe(
			"2 accepted Needs are not included in any departmental plan"
		);
		expect(notice.text()).toContain("Ask the department to raise this with your KenTender administrator.");
		expect(make({ workspace: { ...WORKSPACE, not_included: null } }).find('[data-testid="pln-not-included"]').exists()).toBe(false);
	});

	it("renders the departmental plans card with its relationship heading, rows and caption", () => {
		const w = make();
		const card = w.find('[data-testid="pln-departmental-plans"]');
		expect(card.find(".kt-card-title").text()).toBe("Departmental plans feeding this Annual Plan");
		expect(card.find(".pln-card-subhead").text()).toBe(
			"These are the accepted and pending plans behind the entry above."
		);
		expect(card.findAll("thead th").map((th) => th.text())).toEqual([
			"Department", "Version", "Requirements", "Value", "Status", "",
		]);
		const rows = card.findAll("tbody tr");
		expect(rows).toHaveLength(2);
		expect(rows[1].find(".kt-status").classes()).toContain("is-critical");
		expect(rows[1].find(".kt-status").text()).toBe("Not submitted — window closed");
		expect(rows[1].find("button").text()).toBe("View");
		expect(w.find('[data-testid="pln-count-label"]').text()).toBe("2 departmental plans");
	});

	it("offers no View button on a row the actor cannot open", () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				departmental_plans: [{ ...WORKSPACE.departmental_plans[0], route: null }],
			},
		});
		expect(w.find('[data-testid="pln-departmental-plans"] tbody button').exists()).toBe(false);
	});

	it("shows the schedule-health count only once an Active plan exists (PLN-AC-129)", () => {
		expect(make().find('[data-testid="pln-schedule-health"]').exists()).toBe(false);
		const w = make({ workspace: { ...WORKSPACE, schedule_health: { behind: 1, total: 3 } } });
		expect(w.find('[data-testid="pln-schedule-health"]').text()).toBe("· 1 of 3 items behind baseline");
	});

	it("renders waiting work as neutral text with no control", () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				waiting: [{ item: "Annual Plan awaiting statutory approval", scope: "Annual Procurement Plan FY 2027/28" }],
			},
		});
		const line = w.find('[data-testid="pln-waiting"]');
		expect(line.text()).toBe("Annual Plan awaiting statutory approval · Annual Procurement Plan FY 2027/28");
		expect(line.find("button").exists()).toBe(false);
	});

	it("shows no charts, summary tiles or system support links (§11.2)", () => {
		const w = make();
		expect(w.text()).not.toContain("%");
		expect(w.find("canvas").exists()).toBe(false);
		expect(w.text()).not.toContain("Support workspace");
	});

	it("routes an open-departmental-plan action through its own event", async () => {
		const w = make({
			workspace: {
				...WORKSPACE,
				actionable: [
					{
						headline: "Open departmental plan",
						supporting: "Digital Health",
						action: "Open departmental plan",
						route: ["procurement-planning", "open", "OU-0001"],
					},
				],
			},
		});
		await w.find('[data-testid="pln-work-action-0"]').trigger("click");
		expect(w.emitted("open-departmental-plan")[0][0]).toBe("OU-0001");
		expect(w.emitted("navigate")).toBeUndefined();
	});
});

describe("WorkspaceScreen — PLN-DES-16 states", () => {
	it("renders the Forbidden panel with the exact copy and nothing else (PLN-AC-111..113)", () => {
		const w = make({
			workspace: {
				outcome: "FORBIDDEN",
				forbidden: {
					heading: "You do not have access to Procurement Planning",
					text: "This area needs one of these responsibilities: Procurement Planner, Finance Confirmation Officer, Accounting Officer, the entity's statutory approver, Head of User Department, Departmental Author or Auditor. Ask your KenTender administrator to assign one in System setup.",
				},
			},
		});
		const card = w.find('[data-testid="pln-forbidden"]');
		expect(card.find("h3").text()).toBe("You do not have access to Procurement Planning");
		expect(card.text()).toContain("Ask your KenTender administrator to assign one in System setup.");
		expect(card.find("button").exists()).toBe(false);
		expect(w.find('[data-testid="pln-context-strip"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-departmental-plans"]').exists()).toBe(false);
	});

	it("renders the no-context state without a Procuring Entity mention", () => {
		const w = make({ workspace: { outcome: "NO_CONTEXT", context: {} } });
		const card = w.find('[data-testid="pln-no-context"]');
		expect(card.find("h3").text()).toBe("Procurement Planning is not available");
		expect(card.text()).not.toContain("Procuring Entity");
		expect(card.find("button").exists()).toBe(false);
	});

	it("renders the load-error state with Try again and the support reference", async () => {
		const w = make({ error: "boom", supportRef: "PLN-ERR-20261201-0917" });
		const card = w.find('[data-testid="pln-error"]');
		expect(card.find("h3").text()).toBe("Procurement Planning could not be loaded");
		expect(card.text()).toContain("Support reference: PLN-ERR-20261201-0917");
		await card.find("button").trigger("click");
		expect(w.emitted("reload")).toHaveLength(1);
	});
});
