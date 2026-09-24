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
import PublicationResultScreen from "./PublicationResultScreen.vue";
import ReviewScreen from "./ReviewScreen.vue";
import { READY } from "./ReservationAllocation.fixtures.js";
import SourceEvidenceScreen from "./SourceEvidenceScreen.vue";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const D = "docs/mvp-1-r1/04_planning/design/";

const SCREENS = [
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
				current_issue: null,
				// U01-HOD is the departmental actor reading their own plan and
				// the register beneath it.
				actionable: [{ title: "Certify the departmental plan", meta: "Digital Health · FY 2027/28", action: "Open departmental plan", route: ["departmental-procurement-plan", "DPP-MOH-DHI-2027-001"] }],
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
