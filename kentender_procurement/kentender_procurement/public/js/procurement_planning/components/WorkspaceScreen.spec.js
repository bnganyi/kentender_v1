// PLN-CHG-001 v1.23 §10.3 — WorkspaceScreen component tests (U01 and its
// five variants).
//
// These assert composition, not styling: which regions appear, in what order,
// and which actions are present versus absent. Every label is the server's own
// literal, so nothing here re-derives one.
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

const PLANNER_HEADER = {
	title: "Annual procurement planning",
	description: "Prepare departmental requirements, organise the annual plan and follow its approval.",
};

const DRAFT_ROW = {
	kind: "draft",
	facts: [
		["Current plan", "No current plan yet"],
		["Work", "Draft plan"],
		["Version", "1"],
		["Purchases", "2"],
		["Estimated cost", "KES 130,000,000"],
		["Plan reference", "PLN-MOH-2027-001"],
	],
	note: "This plan is being prepared. It cannot yet be used to authorise procurement.",
	action: "Continue plan",
	action_kind: "primary",
	route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
};

const CURRENT_ROW = {
	kind: "current",
	facts: [
		["Current plan", "Ministry of Health Annual Procurement Plan 2027/28"],
		["Version", "1"],
		["Approved value", "KES 130,000,000"],
		["Status", "Current plan"],
		["Plan reference", "PLN-MOH-2027-001"],
	],
	note: "",
	action: "View current plan",
	action_kind: "secondary",
	route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
};

const UPDATE_ROW = {
	kind: "candidate",
	facts: [
		["Work", "Plan update — Draft"],
		["Version", "2"],
		["Proposed value", "KES 130,000,000"],
		["Change", "Description updated"],
	],
	note: "",
	action: "Continue update",
	action_kind: "primary",
	route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
};

const DEPT_TABLE = {
	heading: "Departmental plans",
	columns: ["Department", "Status", "Requirements", "Estimated cost", "Action"],
	rows: [
		{
			department: "Digital Health",
			status: "Accepted",
			status_kind: "live",
			requirements: 2,
			value: "KES 110,000,000",
			action: "View departmental plan",
			route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"],
		},
		{
			department: "Human Resources Management and Development",
			status: "Accepted",
			status_kind: "live",
			requirements: 1,
			value: "KES 20,000,000",
			action: "View departmental plan",
			route: ["departmental-procurement-plan", "DPP-MOH-HRMD-2027-001"],
		},
	],
	count_label: "2 departmental plans",
	empty_text: "No departmental plans to display.",
};

function workspace(overrides = {}) {
	return {
		outcome: "OK",
		context: CONTEXT,
		window_open: true,
		header: PLANNER_HEADER,
		annual_plan: {
			heading: "Annual plan",
			plan_reference: "PLN-MOH-2027-001",
			title: "Ministry of Health Annual Procurement Plan 2027/28",
			rows: [],
			can_prepare_update: false,
			prepare_update_action: "Prepare plan update",
			update_note: "",
			empty_title: "No annual plan yet",
			empty_text: "The draft annual plan will appear after Procurement accepts a departmental plan.",
			read_only: false,
		},
		current_issue: null,
		your_departmental_plan: null,
		actionable: [],
		waiting: [],
		not_included: null,
		departmental_table: { ...DEPT_TABLE, rows: [] },
		departmental_plans: [],
		...overrides,
	};
}

function make(props = {}) {
	return mount(WorkspaceScreen, {
		props: { loading: false, error: "", supportRef: "", pending: false, workspace: workspace(), ...props },
	});
}

describe("WorkspaceScreen — page states", () => {
	it("shows only the loading skeleton, with no stale rows or actions", () => {
		const w = make({ loading: true });
		expect(w.find('[data-testid="pln-loading"]').exists()).toBe(true);
		expect(w.text()).toContain("Loading procurement planning…");
		expect(w.find('[data-testid="pln-context-strip"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-departmental-table"]').exists()).toBe(false);
	});

	it("paints the denied panel with no header, filter or content behind it", () => {
		const w = make({
			workspace: workspace({
				outcome: "FORBIDDEN",
				forbidden: { heading: "You do not have access to Procurement Planning.", text: "Ask your KenTender administrator." },
			}),
		});
		expect(w.find('[data-testid="pln-forbidden"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-title"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-context-strip"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-annual-plan-empty"]').exists()).toBe(false);
	});

	it("offers Try again on a load failure and never a guessed empty state", () => {
		const w = make({ error: "boom", supportRef: "PLN-1234" });
		expect(w.find('[data-testid="pln-error"]').text()).toContain("Try again. If the problem continues, contact support.");
		expect(w.find('[data-testid="pln-departmental-table"]').exists()).toBe(false);
	});
});

describe("WorkspaceScreen — U01 BASE", () => {
	function base() {
		return make({
			workspace: workspace({
				annual_plan: { ...workspace().annual_plan, rows: [DRAFT_ROW] },
				current_issue: {
					text: "Allocate KES 48,000,000 more to eligible reserved procurement before sending the plan to Finance.",
					action: "Review reserved procurement",
					route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
				},
				departmental_table: DEPT_TABLE,
			}),
		});
	}

	it("leads with the header, then the draft plan row and its plain note", () => {
		const w = base();
		expect(w.find('[data-testid="pln-title"]').text()).toBe("Annual procurement planning");
		const row = w.find('[data-testid="pln-plan-row-draft"]');
		expect(row.text()).toContain("No current plan yet");
		expect(row.text()).toContain("Draft plan");
		expect(row.text()).toContain("KES 130,000,000");
		expect(row.find("button").text()).toBe("Continue plan");
		expect(w.find('[data-testid="pln-plan-note"]').text()).toBe(
			"This plan is being prepared. It cannot yet be used to authorise procurement.",
		);
	});

	it("states the reservation shortfall once, as a sentence with one action", () => {
		const w = base();
		const issue = w.find('[data-testid="pln-current-issue"]');
		expect(issue.text()).toContain("Allocate KES 48,000,000 more to eligible reserved procurement");
		expect(issue.find('[data-testid="pln-current-issue-action"]').text()).toBe("Review reserved procurement");
		// PLN22-AC-006: the required/qualifying/shortfall/basis arithmetic
		// belongs to the Plan check detail, not to this page.
		expect(w.text()).not.toContain("Required allocation");
		expect(w.text()).not.toContain("Planned qualifying allocation");
		expect(w.text()).not.toContain("Budget basis");
	});

	it("renders the departmental table without submission numbers", () => {
		const w = base();
		const headers = w.findAll('[data-testid="pln-departmental-table"] th').map((th) => th.text());
		expect(headers).toEqual(["Department", "Status", "Requirements", "Estimated cost", "Action"]);
		expect(w.findAll('[data-testid="pln-departmental-row"]')).toHaveLength(2);
		expect(w.find('[data-testid="pln-count-label"]').text()).toBe("2 departmental plans");
		expect(w.text()).not.toContain("Submission");
	});

	it("omits the Your actions section entirely when there is no action", () => {
		const w = base();
		expect(w.find('[data-testid="pln-your-actions-heading"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-action"]').exists()).toBe(false);
	});
});

describe("WorkspaceScreen — U01-CURRENT and U01-CURRENT-UPDATE", () => {
	it("offers Prepare plan update beside the section heading when no update exists", () => {
		const w = make({
			workspace: workspace({
				annual_plan: { ...workspace().annual_plan, rows: [CURRENT_ROW], can_prepare_update: true },
				departmental_table: DEPT_TABLE,
			}),
		});
		expect(w.find('[data-testid="pln-prepare-update"]').text()).toBe("Prepare plan update");
		expect(w.find('[data-testid="pln-plan-row-current"]').text()).toContain("Current plan");
		expect(w.find('[data-testid="pln-current-issue"]').exists()).toBe(false);
	});

	it("shows two independent rows, the in-force note between them, and removes the update control", () => {
		const w = make({
			workspace: workspace({
				annual_plan: {
					...workspace().annual_plan,
					rows: [CURRENT_ROW, UPDATE_ROW],
					can_prepare_update: false,
					update_note: "The current plan remains in force while this update is reviewed.",
				},
				departmental_table: DEPT_TABLE,
			}),
		});
		expect(w.find('[data-testid="pln-plan-row-current"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-plan-row-candidate"]').text()).toContain("Plan update — Draft");
		expect(w.find('[data-testid="pln-update-note"]').text()).toBe(
			"The current plan remains in force while this update is reviewed.",
		);
		// Removed, not disabled (§10.3).
		expect(w.find('[data-testid="pln-prepare-update"]').exists()).toBe(false);
	});
});

describe("WorkspaceScreen — U01-NO-PLAN", () => {
	it("shows the empty state and offers no create action", () => {
		const w = make();
		const empty = w.find('[data-testid="pln-annual-plan-empty"]');
		expect(empty.text()).toContain("No annual plan yet");
		expect(empty.text()).toContain("The draft annual plan will appear after Procurement accepts a departmental plan.");
		expect(empty.find("button").exists()).toBe(false);
		expect(w.find('[data-testid="pln-prepare-update"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-departmental-empty"]').text()).toBe("No departmental plans to display.");
	});
});

describe("WorkspaceScreen — U01-DEPARTMENT-AUTHOR and U01-HOD", () => {
	const DEPT_HEADER = {
		title: "Procurement planning",
		description: "Prepare your department's procurement requirements and follow their review.",
	};

	it("uses the departmental header and shows the department's own plan row", () => {
		const w = make({
			workspace: workspace({
				header: DEPT_HEADER,
				your_departmental_plan: {
					heading: "Your departmental plan",
					empty: false,
					facts: [["Department", "Digital Health"], ["Status", "Draft"]],
					action: "Continue departmental plan",
					route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"],
				},
			}),
		});
		expect(w.find('[data-testid="pln-title"]').text()).toBe("Procurement planning");
		const own = w.find('[data-testid="pln-own-plan"]');
		expect(own.text()).toContain("Digital Health");
		expect(own.text()).toContain("FY 2027/28");
		expect(own.find('[data-testid="pln-own-plan-action"]').text()).toBe("Continue departmental plan");
	});

	it("offers Start departmental plan only when no plan exists and intake is open", () => {
		const w = make({
			workspace: workspace({
				header: DEPT_HEADER,
				your_departmental_plan: {
					heading: "Your departmental plan",
					empty: true,
					empty_text: "No departmental plan yet",
					action: "Start departmental plan",
					organisation_unit: "OU-MOH-DHI",
				},
			}),
		});
		expect(w.find('[data-testid="pln-own-plan-empty"]').text()).toBe("No departmental plan yet");
		w.find('[data-testid="pln-start-departmental-plan"]').trigger("click");
		expect(w.emitted("open-departmental-plan")[0]).toEqual(["OU-MOH-DHI"]);
	});

	it("puts the HoD's required outcome above the plan, with one action", () => {
		const w = make({
			workspace: workspace({
				header: DEPT_HEADER,
				actionable: [
					{
						headline: "Review and submit",
						supporting: "Digital Health FY 2027/28",
						action: "Review departmental plan",
						route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"],
						facts: [{ label: "Departmental plan", value: "Digital Health FY 2027/28" }],
					},
				],
			}),
		});
		expect(w.find('[data-testid="pln-your-actions-heading"]').text()).toBe("Your action");
		const action = w.find('[data-testid="pln-action"]');
		expect(action.text()).toContain("Review and submit");
		expect(action.find('[data-testid="pln-action-button"]').text()).toBe("Review departmental plan");
	});
});
