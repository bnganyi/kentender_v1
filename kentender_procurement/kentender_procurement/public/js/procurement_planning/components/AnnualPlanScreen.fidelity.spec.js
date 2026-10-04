// Structural fidelity for U07, against Artboards-U07-U08.dc.html.
//
// The companion to AnnualPlanScreen.spec.js: that file checks what the screen
// says, this one checks what it is built out of. The landmark gate compares
// the artboard's ordered landmark *texts*, so it cannot see a container at
// all — the `.kt-group` around Plan checks was dropped and nothing failed,
// because a wrapper has no text of its own (found live 24 Sep 2026).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import AnnualPlanScreen from "./AnnualPlanScreen.vue";
import { BASE, READY } from "./ReservationAllocation.fixtures.js";
import { FINANCE_CONFIRMED, FINANCE_NOT_REQUESTED, FIT_OVER, FIT_WITHIN, METHOD_BLOCKED, OVER_BUDGET, UPSTREAM, WAITING_BUDGET, WAITING_SIGNATURE, planJourney } from "./guidance.fixtures.js";
import { boardSkeleton } from "../../../../../../tests/ui/fidelity/board.js";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../../../../../tests/ui/fidelity/skeleton.js";
import { DEPARTURES } from "../../../../../../tests/ui/fidelity/departures/procurement-planning.js";

const BOARD = "docs/mvp-1-r1/04_planning/design/Artboards-U07-U08.dc.html";

const ITEM = {
	plan_item_id: "PPI-MOH-2027-033",
	title: "Clinical laptops",
	quantity_number: "250",
	unit_label: "Each",
	value_display: "KES 50,000,000",
	completion_display: "31 Dec 2027",
	current_work: "Ready",
	route: ["procurement-plan-item", "PPI-MOH-2027-033"],
};

function plan(overrides = {}) {
	return {
		outcome: "OK",
		plan_reference: "PLN-MOH-2027-001",
		version_number: 1,
		version_status: "Draft",
		record_version: 3,
		mutable: true,
		header: { title: "Ministry of Health Annual Procurement Plan 2027/28", badge: "Draft" },
		plan_items: [ITEM],
		unallocated_sources: [],
		// PLN v1.27 U07 BASE: the method is the pre-Finance blocker (next-step
		// block); the reservation shortfall is a signature blocker (plain row);
		// budget fit and Finance confirmation replace the Funding cell.
		plan_checks: [
			{ label: "Reserved procurement", result: "KES 39,000,000 more qualifying allocation required", detail: "Resolve this before the plan can be signed and submitted.", kind: "critical", action: "Review reserved procurement", route: ["annual-procurement-plan", "PLN-MOH-2027-001"] },
			{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null },
		],
		next_step: METHOD_BLOCKED,
		journey: planJourney("preparation", { blocked: true, holder: "Mercy Kilonzo", upstream: UPSTREAM }),
		budget_fit: FIT_WITHIN,
		finance_confirmation: FINANCE_NOT_REQUESTED,
		summary: { reservation_allocation: BASE },
		submission_issues: [],
		changes: { is_initial: true },
		history: [{ title: "Digital Health accepted", meta: "Mercy Kilonzo · 27 Nov 2026" }],
		can_request_funding: false,
		can_sign_and_submit: false,
		can_cancel_update: false,
		open_task: null,
		...overrides,
	};
}

function built(props = {}) {
	const wrapper = mount(AnnualPlanScreen, {
		props: { plan: plan(), selected: [], pending: false, errorSummary: "", ...props },
	});
	return skeletonOf(wrapper.element.querySelector(".kt-page"));
}

function check(variant, props) {
	const result = compareSkeletons(boardSkeleton(BOARD, variant), built(props), {
		departures: DEPARTURES[`AnnualPlanScreen#${variant}`] || [],
	});
	return { result, message: formatMismatch(variant, result) };
}

describe("AnnualPlanScreen — the containers U07 draws", () => {
	it("builds U07 out of the board's own containers", () => {
		const { result, message } = check("U07");
		expect(message, message).toBe("");
		expect(result).toEqual({ missing: [], extra: [] });
	});

	it("builds U07-FINANCE-COMPLETE out of the board's own containers", () => {
		const { result, message } = check("U07-FINANCE-COMPLETE", {
			plan: plan({
				can_request_funding: false,
				plan_checks: [{ label: "Schedule", result: "Both purchases meet their departmental deadlines", kind: "live", route: null }],
				summary: { reservation_allocation: READY },
				next_step: WAITING_SIGNATURE,
				journey: planJourney("signature", { holder: "Charles Mutiso" }),
				finance_confirmation: FINANCE_CONFIRMED,
			}),
		});
		expect(message, message).toBe("");
		expect(result).toEqual({ missing: [], extra: [] });
	});

	it("builds U07-UPDATE-OVER-BUDGET out of the board's own containers", () => {
		const { result, message } = check("U07-UPDATE-OVER-BUDGET", {
			plan: plan({
				is_successor: true,
				current_version_number: 1,
				version_number: 2,
				plan_checks: [{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null }],
				summary: { reservation_allocation: READY },
				next_step: OVER_BUDGET,
				journey: planJourney("preparation", { blocked: true, holder: "Mercy Kilonzo", upstream: { ...UPSTREAM, label: "5 departmental requirements included" } }),
				budget_fit: FIT_OVER,
				changes: {
					is_initial: false,
					rows: [
						{ plan_item_id: "PPI-MOH-2027-051", title: "Digital health workforce certification programme", field: "Estimated cost", current: "Not in the current plan", proposed: "KES 10,000,000" },
						{ plan_item_id: "PPI-MOH-2027-052", title: "Digital health training assessment materials", field: "Estimated cost", current: "Not in the current plan", proposed: "KES 2,000,000" },
					],
				},
			}),
		});
		expect(message, message).toBe("");
		expect(result).toEqual({ missing: [], extra: [] });
	});

	it("builds U07-WAITING-BUDGET-REVISION out of the board's own containers", () => {
		const { result, message } = check("U07-WAITING-BUDGET-REVISION", {
			plan: plan({
				is_successor: true,
				current_version_number: 1,
				version_number: 2,
				plan_checks: [{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null }],
				summary: { reservation_allocation: READY },
				next_step: WAITING_BUDGET,
				journey: planJourney("preparation", { blocked: true, holder: "Mercy Kilonzo", upstream: { ...UPSTREAM, label: "5 departmental requirements included" } }),
				budget_fit: FIT_OVER,
				changes: {
					is_initial: false,
					rows: [
						{ plan_item_id: "PPI-MOH-2027-051", title: "Digital health workforce certification programme", field: "Estimated cost", current: "Not in the current plan", proposed: "KES 10,000,000" },
						{ plan_item_id: "PPI-MOH-2027-052", title: "Digital health training assessment materials", field: "Estimated cost", current: "Not in the current plan", proposed: "KES 2,000,000" },
					],
				},
			}),
		});
		expect(message, message).toBe("");
		expect(result).toEqual({ missing: [], extra: [] });
	});
});
