// Structural fidelity for the Procurement Planning screens, against their own
// `.dc.html` artboards.
//
// One table, one assertion. The landmark gate compares the artboard's ordered
// landmark *texts*, so no container is visible to it: the `.kt-group` around
// Plan checks was dropped, eight disclosure heads lost their title row and
// chevron, and a heading was demoted to a label — all while every fidelity
// assertion passed (found live 24 Sep 2026; the U09 precedent is `cf968ac9`).
//
// Each row names the component, the board variant it claims, and the props
// that put it in the state that board drew. A board variant is a snapshot of
// particular data, so a section the fixture has nothing for will not render —
// that is what the departures registry's per-variant entries are for.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import { boardSkeleton } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/procurement-planning.js";

import CorrectionRequestsScreen from "./CorrectionRequestsScreen.vue";
import DppValidationScreen from "./DppValidationScreen.vue";
import FinanceTaskScreen from "./FinanceTaskScreen.vue";
import ProgressScreen from "./ProgressScreen.vue";
import ReviewScreen from "./ReviewScreen.vue";
import { READY } from "./ReservationAllocation.fixtures.js";
import {
	AO_TURN, AUTHOR_DRAFT_TURN, CLASSIFICATION_PROMPT, FINANCE_TURN, WAITING_AO, planJourney, CLOSED_BLOCKED, CORRECTION_TURN, HOD_TURN, REVIEW_SEGREGATED, REVIEW_TURN, dppJourney,
} from "./guidance.fixtures.js";
import DppPlanScreen from "./DppPlanScreen.vue";
import SourceEvidenceScreen from "./SourceEvidenceScreen.vue";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const D = "docs/mvp-1-r1/04_planning/design/";

// PLN v1.27 §10.3 — the U01 Planner variants this cycle changed: the BASE
// issue region (D2) and the two over-budget update rows. Server-shaped.
const U01_CONTEXT = {
	financial_year: "2027-2028",
	financial_year_label: "FY 2027/28",
	financial_years: [{ id: "2027-2028", label: "FY 2027/28" }],
	resolved_financial_year_source: "default",
};
const U01_DEPARTMENTS = {
	heading: "Departmental plans",
	columns: ["Department", "Status", "Requirements", "Estimated cost", "Action"],
	rows: [
		{ department: "Digital Health", status: "Accepted", status_kind: "live", requirements: 2, value: "KES 110,000,000", action: "View departmental plan", route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"] },
		{ department: "Human Resources Management and Development", status: "Accepted", status_kind: "live", requirements: 1, value: "KES 20,000,000", action: "View departmental plan", route: ["departmental-procurement-plan", "DPP-MOH-HRMD-2027-001"] },
	],
	count_label: "2 departmental plans",
	empty_text: "No departmental plans to display.",
};
const U01_CURRENT_ROW = {
	kind: "current",
	facts: [["Current plan", "Ministry of Health Annual Procurement Plan 2027/28"], ["Version", "1"], ["Approved value", "KES 130,000,000"], ["Status", "Current plan"], ["Plan reference", "PLN-MOH-2027-001"]],
	note: "", action: "View current plan", action_kind: "secondary", route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
};
function u01(rows, extra = {}) {
	return {
		workspace: {
			outcome: "OK",
			context: U01_CONTEXT,
			window_open: true,
			header: { title: "Annual procurement planning", description: "Prepare departmental requirements, organise the annual plan and follow its approval." },
			annual_plan: {
				heading: "Annual plan", plan_reference: "PLN-MOH-2027-001", title: "Ministry of Health Annual Procurement Plan 2027/28",
				rows, can_prepare_update: false, prepare_update_action: "Prepare plan update",
				update_note: rows.length > 1 ? "The current plan remains in force while this update is reviewed." : "",
				empty_title: "No annual plan yet", empty_text: "", read_only: false,
			},
			issues: [],
			your_departmental_plan: null,
			actionable: [],
			waiting: [],
			not_included: null,
			departmental_table: U01_DEPARTMENTS,
			departmental_plans: [],
			...extra,
		},
	};
}
const u01Update = (narrative, action = "Continue update", action_kind = "primary") => ({
	kind: "candidate",
	facts: [["Work", "Plan update — Draft"], ["Version", "2"], ["Proposed value", "KES 142,000,000"]],
	narrative, note: "", action, action_kind, route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
});

// PLN v1.27 §10.5 — U06 with its next step and DPP journey (server-shaped).
const U06_ROW = (id, title, amount, line) => ({
	entry_id: id, title, quantity_number: "1", unit_label: "Programme", required_by_display: "31 Aug 2027",
	amount_display: amount, budget_line_display: line, not_proceeding: false, not_proceeding_reason: "",
});
function u06(overrides = {}) {
	return {
		task: {
			outcome: "OK", task: "DPPT-1", status: "Open", can_decide: true, maker_checker_blocked: false,
			header: { reference_line: "DPP-MOH-DHI-2027-001 · Submission 1" },
			context: {
				department: "Digital Health", financial_year: "FY 2027/28", submitted_by: "Julia Njeri", submitted_at: "25 Nov 2026, 10:30 EAT",
				included_requirements: 2, included_cost_display: "KES 110,000,000", excluded_requirements: 0,
			},
			entries: [
				U06_ROW("E1", "National digital health infrastructure upgrade", "KES 80,000,000", "Digital health infrastructure programme · MOH-BL-DHI-2027"),
				U06_ROW("E2", "Clinical deployment laptops for digital health rollout", "KES 30,000,000", "Digital health workforce development · MOH-BL-HWD-2027"),
			],
			requirement_types: [{ requirement_type: "Goods", procurement_category: "Goods" }, { requirement_type: "Works", procurement_category: "Works" }],
			stale_sources: [],
			certification: { text: "I certify this plan." },
			next_step: REVIEW_TURN,
			journey: dppJourney("review", { holder: "Mercy Kilonzo" }),
			classification_prompt: CLASSIFICATION_PROMPT,
			...overrides,
		},
		classifications: {},
	};
}

// PLN v1.27 §10.4 — U02–U05 with their next step and DPP journey.
const DPP_ROW = (over) => ({
	entry_id: "E1", title: "National digital health infrastructure upgrade", source_reference: "NDS-MOH-2027-0001 · Revision 1",
	quantity_number: "1", unit_label: "Programme", required_by_display: "31 Aug 2027", amount_display: "Not entered",
	status: "Funding details needed", status_kind: "attention", disposition: "Proceeding", not_proceeding_reason: "",
	action: "Enter funding details", issues: [], ...over,
});
function dpp(over = {}) {
	return {
		plan: {
			outcome: "OK", access: "author", mutable: true, can_submit: false, can_create_update: false, is_correction: false,
			header: { badge: "Draft", badge_kind: "draft" },
			context: { department: "DHI — Digital Health", department_name: "Digital Health", financial_year: "FY 2027/28", window: { state: "Open", display: "Open" } },
			entries: [
				DPP_ROW(),
				DPP_ROW({ entry_id: "E2", title: "Clinical deployment laptops for digital health rollout", amount_display: "KES 30,000,000", status: "Included", status_kind: "live", action: "Review details" }),
			],
			included_cost_display: "KES 30,000,000",
			certification: { show: false }, submit_hint: "Your Head of Department must review and submit this plan.",
			open_task: null,
			next_step: AUTHOR_DRAFT_TURN,
			journey: dppJourney("preparation", { holder: "Grace Wanjiku", reduced: true }),
			...over,
		},
		pending: false, certified: false, errorSummary: "",
	};
}

// PLN v1.27 §10.12 — U13 with its reduced tracker.
const SCREENS = [
	// U13 is not compared to a board in v1.31: Artboards-U12-U13 still draws the v1.30 Accounting Officer Treasury form, and the
	// new variants need new artboards before design sign-off (PLN-CHG-001 v1.31 §17.2). The screen is covered by PublicationResultScreen.spec.js.
	{ name: "DppPlanScreen", component: DppPlanScreen, board: `${D}Artboards-U02-U05.dc.html`, variant: "U02-AUTHOR-DRAFT", props: dpp() },
	{
		name: "DppPlanScreen", component: DppPlanScreen, board: `${D}Artboards-U02-U05.dc.html`, variant: "U02-CLOSED",
		props: dpp({
			context: { department: "DHI — Digital Health", department_name: "Digital Health", financial_year: "FY 2027/28", window: { state: "Closed", display: "Closed" } },
			next_step: CLOSED_BLOCKED, journey: dppJourney("preparation", { holder: "Grace Wanjiku" }),
		}),
	},
	{
		name: "DppPlanScreen", component: DppPlanScreen, board: `${D}Artboards-U02-U05.dc.html`, variant: "U05-HOD",
		props: dpp({
			access: "hod", can_submit: true, included_cost_display: "KES 110,000,000",
			entries: [DPP_ROW({ amount_display: "KES 80,000,000", status: "Included", status_kind: "live", action: "View details" }), DPP_ROW({ entry_id: "E2", amount_display: "KES 30,000,000", status: "Included", status_kind: "live", action: "View details" })],
			certification: { show: true, text: "I certify this plan.", checkbox_label: "I confirm this certification" },
			submit_hint: "", next_step: HOD_TURN, journey: dppJourney("certification", { holder: "Julia Njeri" }),
		}),
	},
	{
		name: "DppPlanScreen", component: DppPlanScreen, board: `${D}Artboards-U02-U05.dc.html`, variant: "U05-CORRECTION",
		props: dpp({
			access: "hod", can_submit: true, is_correction: true, returned_submission_number: 1, candidate_submission_number: 2,
			entries: [DPP_ROW({ amount_display: "KES 80,000,000", status: "Included", status_kind: "live", action: "View details" }), DPP_ROW({ entry_id: "E2", amount_display: "KES 30,000,000", status: "Included", status_kind: "live", action: "View details", issues: [{ problem: "", correction: "Explain the estimate." }] })],
			certification: { show: true, text: "I certify this plan.", checkbox_label: "I confirm this certification" },
			submit_hint: "", next_step: CORRECTION_TURN, journey: dppJourney("preparation"),
		}),
	},
	{ name: "DppValidationScreen", component: DppValidationScreen, board: `${D}Artboards-U06.dc.html`, variant: "U06", props: u06() },
	{
		name: "DppValidationScreen", component: DppValidationScreen, board: `${D}Artboards-U06.dc.html`, variant: "U06-SEGREGATION",
		props: u06({ can_decide: false, maker_checker_blocked: true, next_step: REVIEW_SEGREGATED, journey: dppJourney("review") }),
	},
	{
		name: "WorkspaceScreen",
		component: WorkspaceScreen,
		board: `${D}Artboards-U01.dc.html`,
		variant: "U01",
		props: u01(
			[{
				kind: "draft",
				facts: [["Current plan", "No current plan yet"], ["Work", "Draft plan"], ["Version", "1"], ["Purchases", "2"], ["Estimated cost", "KES 130,000,000"], ["Plan reference", "PLN-MOH-2027-001"]],
				note: "This plan is being prepared. It cannot yet be used to authorise procurement.",
				action: "Continue plan", action_kind: "primary", route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
			}],
			{
				issues: [
					{ tone: "dominant", text: "1 purchase needs a procurement method. Choose it before sending the plan to Finance.", strong: "1 purchase needs a procurement method.", action: "Choose a procurement method", route: ["procurement-plan-item", "PPI-MOH-2027-021"] },
					{ tone: "quiet", text: "Reserved procurement is below the required allocation by KES 39,000,000. Resolve this before the plan can be signed and submitted.", strong: "KES 39,000,000", action: "Review reserved procurement", route: ["annual-procurement-plan", "PLN-MOH-2027-001"] },
				],
			},
		),
	},
	{
		name: "WorkspaceScreen",
		component: WorkspaceScreen,
		board: `${D}Artboards-U01.dc.html`,
		variant: "U01-CURRENT-UPDATE-OVER-BUDGET",
		props: u01([U01_CURRENT_ROW, u01Update({ tone: "blocked", headline: "Over budget by KES 2,000,000 on Digital health workforce development", since: "" })]),
	},
	{
		name: "WorkspaceScreen",
		component: WorkspaceScreen,
		board: `${D}Artboards-U01.dc.html`,
		variant: "U01-CURRENT-UPDATE-WAITING-BUDGET",
		props: u01(
			[U01_CURRENT_ROW, u01Update({ tone: "waiting", headline: "Waiting for Josphat Mwangi (Budget Officer) to revise the budget line", since: "15 Dec 2026, 10:00 EAT" }, "View update", "secondary")],
		),
	},
	{
		name: "WorkspaceScreen",
		component: WorkspaceScreen,
		board: `${D}Artboards-U01.dc.html`,
		variant: "U01-HOD",
		props: {
			workspace: {
				outcome: "OK",
				header: { title: "Procurement planning", description: "Prepare and govern the annual plan." },
				financial_year: "2027-2028",
				financial_years: [{ id: "2027-2028", label: "FY 2027/28" }],
				tasks: [],
				plan: null,
				departmental_plans: [{ dpp_reference: "DPP-MOH-DHI-2027-001", department: "Digital Health", state: "Accepted", kind: "live", entries: 2, value_display: "KES 50,000,000" }],
				notices: [],
				issues: [],
				// U01-HOD is the departmental actor reading their own plan and
				// the register beneath it.
				actionable: [{ title: "Certify the departmental plan", meta: "Digital Health · FY 2027/28", action: "Open departmental plan", route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"] }],
				actionable_heading: "1 departmental plan requires your decision",
				your_departmental_plan: { dpp_reference: "DPP-MOH-DHI-2027-001", department: "Digital Health", state: "Accepted", kind: "live" },
			},
		},
	},
	{
		name: "FinanceTaskScreen",
		component: FinanceTaskScreen,
		board: `${D}Artboards-U10.dc.html`,
		variant: "U10",
		props: {
			task: {
				outcome: "OK",
				header: { title: "Confirm funding for the annual plan", badge: "Awaiting Finance" },
				plan_reference: "PLN-MOH-2027-001",
				version: { number: 1 },
				budget_reference: "MOH-BUD-2027-001",
				as_at_display: "4 Dec 2026, 10:00 EAT",
				summary: { plan_items: 2, value_display: "KES 130,000,000", lines_used: 2 },
				rows: [{ budget_line: "MOH-BL-DHI-2027", title: "Digital health", approved_display: "KES 100,000,000", planned_display: "KES 80,000,000", available_display: "KES 20,000,000", result: "Within budget", result_kind: "live" }],
				statement: { within_approved: true },
				status: "Open",
				can_decide: true,
				can_confirm: true,
				decided: false,
				next_step: FINANCE_TURN,
				journey: planJourney("funding", { holder: "Josphat Mwangi" }),
			},
		},
	},
	{
		name: "ReviewScreen",
		component: ReviewScreen,
		board: `${D}Artboards-U11.dc.html`,
		variant: "U11-AO",
		props: {
			task: {
				outcome: "OK",
				header: { title: "Adopt the annual procurement plan", badge: "Awaiting Accounting Officer" },
				plan_reference: "PLN-MOH-2027-001",
				version_number: 1,
				stage: "Accounting Officer adoption",
				next_step: AO_TURN,
				journey: planJourney("ao", { holder: "Amina Hassan" }),
				decision_summary: {
					value_display: "KES 130,000,000",
					purchases: 2,
					departments: 2,
					funding: "Within each approved budget line",
					funding_kind: "live",
					reservation: "Required allocation met",
					reservation_kind: "live",
					schedule: "All purchases meet departmental deadlines",
					schedule_kind: "live",
					issues: [],
				},
				rows: [{ plan_item_id: "PPI-MOH-2027-001", title: "Laptops", value_display: "KES 50,000,000", department: "Digital Health", method: "Open Tender", result: "Within budget", result_kind: "live", detail: [{ label: "Budget line", value: "MOH-BL-DHI-2027" }] }],
				accountability: { prepared_by: "Mercy Kilonzo", prepared_at: "3 Dec 2026", confirmed_by: "Josphat Mwangi", confirmed_at: "4 Dec 2026" },
				funding_evidence: [{ label: "Budget", value: "MOH-BUD-2027-001" }],
				reservation: READY,
				changes: { is_initial: true },
				history: [],
				status: "Open",
				can_decide: true,
				can_download_review_pack: true,
				can_decide_positive: true,
			},
		},
	},
	{
		name: "ReviewScreen",
		component: ReviewScreen,
		board: `${D}Artboards-U11.dc.html`,
		variant: "U11-PLANNER",
		props: {
			task: {
				outcome: "OK",
				header: { title: "Adopt the annual procurement plan", badge: "Awaiting Accounting Officer" },
				plan_reference: "PLN-MOH-2027-001",
				version_number: 1,
				stage: "Accounting Officer adoption",
				next_step: WAITING_AO,
				journey: planJourney("ao", { holder: "Amina Hassan" }),
				decision_summary: {
					value_display: "KES 130,000,000",
					purchases: 2,
					departments: 2,
					funding: "Within each approved budget line",
					funding_kind: "live",
					reservation: "Required allocation met",
					reservation_kind: "live",
					schedule: "All purchases meet departmental deadlines",
					schedule_kind: "live",
					issues: [],
				},
				rows: [{ plan_item_id: "PPI-MOH-2027-001", title: "Laptops", value_display: "KES 50,000,000", department: "Digital Health", method: "Open Tender", result: "Within budget", result_kind: "live", detail: [{ label: "Budget line", value: "MOH-BL-DHI-2027" }] }],
				accountability: { prepared_by: "Mercy Kilonzo", prepared_at: "3 Dec 2026", confirmed_by: "Josphat Mwangi", confirmed_at: "4 Dec 2026" },
				funding_evidence: [{ label: "Budget", value: "MOH-BUD-2027-001" }],
				reservation: READY,
				changes: { is_initial: true },
				history: [],
				status: "Open",
				can_decide: false,
				can_download_review_pack: true,
				can_decide_positive: true,
			},
		},
	},
	{
		name: "SourceEvidenceScreen",
		component: SourceEvidenceScreen,
		board: `${D}Artboards-U12-U13.dc.html`,
		variant: "U12",
		props: {
			evidence: {
				outcome: "OK",
				title: "Clinical training laptops",
				need_reference: "NDS-MOH-2027-0003",
				need_revision_number: 2,
				department: "Digital Health",
				budget_line_reference: "MOH-BL-DHI-2027",
				budget_line_name: "Digital health infrastructure",
				quantity_display: "100 Each",
				required_by_display: "31 Dec 2027",
				amount_display: "KES 20,000,000",
				funding_source: "Exchequer",
				certified_by: "Peter Kimani",
				certified_at_display: "27 Nov 2026, 14:00 EAT",
				accepted_by: "Mercy Kilonzo",
				accepted_at_display: "28 Nov 2026, 09:00 EAT",
				classification: "Goods",
				record_details: [{ label: "Recorded", value: "27 Nov 2026" }],
			},
		},
	},
	{
		name: "ProgressScreen",
		component: ProgressScreen,
		board: `${D}Artboards-U14-U16.dc.html`,
		variant: "U14",
		props: {
			progress: {
				outcome: "OK",
				plan_reference: "PLN-MOH-2027-001",
				version_number: 1,
				status: "Active",
				financial_year_label: "FY 2027/28",
				items: [{ plan_item_id: "PPI-MOH-2027-001", title: "Laptops", planned_display: "KES 50,000,000", covered_display: "KES 0", uncovered_display: "KES 50,000,000", stage: "Not started", proceedings: [] }],
			},
		},
	},
	{
		name: "CorrectionRequestsScreen",
		component: CorrectionRequestsScreen,
		board: `${D}Artboards-U14-U16.dc.html`,
		variant: "U16",
		props: {
			task: {
				outcome: "OK",
				title: "Clinical training laptops",
				plan_item_id: "PPI-MOH-2027-001",
				version_number: 1,
				hold: { active: true, text: "Procurement is held while this is resolved.", remaining: 1 },
				requests: [{ request_id: "PCR-001", raised_by: "Mercy Kilonzo", raised_at_display: "5 Dec 2026", reason: "Quantity changed", state: "Open", kind: "attention" }],
			},
		},
	},
];

describe.each(SCREENS)("$name — the containers $variant draws", ({ name, component, board, variant, props }) => {
	it("is built out of the board's own containers", () => {
		const wrapper = mount(component, { props });
		const page = wrapper.element.querySelector(".kt-page");
		expect(page, `${name}: renders no .kt-page for ${variant}`).toBeTruthy();
		const result = compareSkeletons(boardSkeleton(board, variant), skeletonOf(page), {
			departures: DEPARTURES[`${name}#${variant}`] || [],
		});
		const message = formatMismatch(`${name} / ${variant}`, result);
		expect(message, message).toBe("");
	});
});

// Not a board comparison: a rule about the vocabulary itself, which the board
// cannot state because it never draws these classes wrongly. A disclosure with
// no head, or a head with no way to open it, is a defect on any screen.
describe("the disclosure contract, everywhere", () => {
	it.each(SCREENS)("$name gives every disclosure a title row and a chevron", ({ component, props }) => {
		const wrapper = mount(component, { props });
		const heads = wrapper.element.querySelectorAll(".kt-disclosure-head");
		for (const head of heads) {
			expect(head.querySelector(".kt-disclosure-title-row"), `${head.textContent.trim()}: no title row`).toBeTruthy();
			expect(head.querySelector(".kt-disclosure-chevron"), `${head.textContent.trim()}: no chevron`).toBeTruthy();
		}
	});

	it.each(SCREENS)("$name never leaves a disclosure body without its disclosure", ({ component, props }) => {
		const wrapper = mount(component, { props });
		for (const body of wrapper.element.querySelectorAll(".kt-disclosure-body")) {
			expect(body.closest(".kt-disclosure"), "a disclosure body outside any disclosure").toBeTruthy();
		}
	});
});
