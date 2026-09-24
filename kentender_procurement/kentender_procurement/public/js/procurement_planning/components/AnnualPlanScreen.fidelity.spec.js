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
		// The state the board drew: one failing check and two quiet ones.
		plan_checks: [
			{ label: "Funding", result: "Not yet checked", kind: "neutral", route: null },
			{ label: "Reserved procurement", result: "KES 139,494 more qualifying allocation required", kind: "critical", action: "Review reserved procurement", route: ["annual-procurement-plan", "PLN-MOH-2027-001"] },
			{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null },
		],
		summary: { reservation_allocation: BASE },
		submission_issues: [],
		changes: { is_initial: true },
		history: [{ title: "Digital Health accepted", meta: "Mercy Kilonzo · 27 Nov 2026" }],
		can_request_funding: false,
		can_sign_and_submit: false,
		can_cancel_update: false,
		open_task: null,
		waiting_on: { notice: "", people: [], unassigned: "" },
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
				plan_checks: [{ label: "Funding", result: "Within each approved budget line", kind: "live", route: null }],
				summary: { reservation_allocation: READY },
				waiting_on: { notice: "Ready for the Head of Procurement Function to sign and submit", people: ["Charles Mutiso"], unassigned: "" },
			}),
		});
		expect(message, message).toBe("");
		expect(result).toEqual({ missing: [], extra: [] });
	});
});
