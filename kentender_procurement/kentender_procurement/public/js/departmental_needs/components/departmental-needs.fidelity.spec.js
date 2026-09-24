// Structural fidelity for the Departmental Needs screens.
//
// This module's board is an earlier export than Planning's and carries almost
// none of the container vocabulary: `.kt-page`, `.kt-region`, `.kt-group`,
// `.kt-field`, `.kt-table` do not appear in `NDS Artboards.dc.html` at all —
// they were extracted *from* that board afterwards and added to the live
// stylesheet, so the board draws them as unclassed divs with inline styles.
//
// So the comparison runs in two halves:
//
//  1. What the board *does* carry — `.field`, `.kt-notice`, `.kt-meta-row`,
//     the whole `.kt-disclosure` family, `.kt-timeline`, `.table`. That is
//     still enough to catch the defect class that has actually shipped: an
//     editable field rebuilt as a read-only fact row, and a disclosure head
//     with no title row and no chevron.
//  2. Rules about the vocabulary itself, which no board can state because a
//     board never draws them wrongly. These are cross-checks against the
//     module's own consistency, not against the drawing.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import { boardSkeleton, needsScope } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/departmental-needs.js";

import NeedDetailScreen from "./NeedDetailScreen.vue";
import NeedEditorScreen from "./NeedEditorScreen.vue";
import ReviewTaskScreen from "./ReviewTaskScreen.vue";
import WithdrawalReviewScreen from "./WithdrawalReviewScreen.vue";
import WorkspaceScreen from "./WorkspaceScreen.vue";

const BOARD = "docs/mvp-1-r1/01_departmental_needs/design/NDS Artboards.dc.html";

const NEED = {
	need_reference: "NDS-MOH-2027-0003",
	title: "Clinical training laptops",
	description: "Laptops for clinical training.",
	justification: "The training programme cannot run without them.",
	quantity_number: "100",
	unit: "Each",
	required_by: "2027-12-31",
	estimated_amount: "20000000",
	status: "Draft",
	revision_number: 2,
	department: "Digital Health",
	financial_year: "2027-2028",
};

const SCREENS = [
	{
		name: "NeedEditorScreen",
		component: NeedEditorScreen,
		variant: "NDS-DES-04",
		// NDS-DES-04 is the returned correction: the reason notice at the top,
		// the six fields, and the record-details disclosure beneath them.
		props: {
			mode: "correct",
			need: NEED,
			revision: { revision_number: 2 },
			context: { department: "Digital Health", financial_year_label: "FY 2027/28" },
			returnReason: {
				text: "The quantity does not match the training plan.",
				actor_label: "Peter Kimani",
				occurred_label: "28 Nov 2026, 14:00 EAT",
			},
			history: [{ title: "Returned for correction", meta: "Peter Kimani · 28 Nov 2026" }],
		},
	},
];

describe.each(SCREENS)("$name — the structure $variant carries", ({ name, component, variant, props }) => {
	it("is built out of the board's own elements", () => {
		const wrapper = mount(component, { props });
		const result = compareSkeletons(boardSkeleton(BOARD, variant, needsScope), skeletonOf(wrapper.element), {
			departures: DEPARTURES[`${name}#${variant}`] || [],
		});
		const message = formatMismatch(`${name} / ${variant}`, result);
		expect(message, message).toBe("");
	});
});

// The module's own vocabulary, checked across every screen. The board cannot
// state these because it never draws them wrongly; the build did, five times
// for the heading rule alone (found live 24 Sep 2026).
const ALL = [
	{ name: "WorkspaceScreen", component: WorkspaceScreen, props: { workspace: { outcome: "OK", needs: [], filters: {}, financial_years: [], organisation_units: [], statuses: [], can_create: true, header: { title: "My needs", description: "Record what your department needs." } } } },
	{ name: "NeedEditorScreen", component: NeedEditorScreen, props: SCREENS[0].props },
	{ name: "NeedDetailScreen", component: NeedDetailScreen, props: { need: { outcome: "OK", ...NEED, history: [], can_edit: false, disposition: { recorded: false } } } },
	{ name: "ReviewTaskScreen", component: ReviewTaskScreen, props: { task: { outcome: "OK", need: NEED, submitted_by: "Mercy Kilonzo", submitted_at_display: "27 Nov 2026", can_decide: true } } },
	{ name: "WithdrawalReviewScreen", component: WithdrawalReviewScreen, props: { task: { outcome: "OK", need: NEED, reason: "No longer required", requested_by: "Mercy Kilonzo", dependency: { included: false }, can_decide: true } } },
];

describe("the shared vocabulary, on every screen", () => {
	it.each(ALL)("$name titles every section with a region", ({ component, props }) => {
		const wrapper = mount(component, { props });
		for (const heading of wrapper.element.querySelectorAll("h2")) {
			const section = heading.parentElement;
			expect(
				section && section.classList.contains("kt-region"),
				`"${heading.textContent.trim()}" is a section heading in a bare div, so nothing styles it`,
			).toBe(true);
		}
	});

	it.each(ALL)("$name gives every disclosure a title row and a chevron", ({ component, props }) => {
		const wrapper = mount(component, { props });
		for (const head of wrapper.element.querySelectorAll(".kt-disclosure-head")) {
			expect(head.querySelector(".kt-disclosure-title-row"), `${head.textContent.trim()}: no title row`).toBeTruthy();
			expect(head.querySelector(".kt-disclosure-chevron"), `${head.textContent.trim()}: no chevron`).toBeTruthy();
		}
	});

	it.each(ALL)("$name never leaves a disclosure body without its disclosure", ({ component, props }) => {
		const wrapper = mount(component, { props });
		for (const body of wrapper.element.querySelectorAll(".kt-disclosure-body")) {
			expect(body.closest(".kt-disclosure"), "a disclosure body outside any disclosure").toBeTruthy();
		}
	});

	// AGENTS.md §6.6: editable controls are fields, derived values are facts.
	// Ten defects shipped on the Planning purchase editor because a form was
	// built out of the read-only fact primitive, and every landmark assertion
	// still passed.
	it.each(ALL)("$name never puts an editable control inside a read-only fact", ({ component, props }) => {
		const wrapper = mount(component, { props });
		for (const fact of wrapper.element.querySelectorAll(".kt-meta-value")) {
			expect(
				fact.querySelector("input, select, textarea"),
				`an editable control inside a .kt-meta-value ("${(fact.textContent || "").slice(0, 40).trim()}")`,
			).toBeNull();
		}
	});
});
