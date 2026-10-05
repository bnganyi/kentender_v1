// PLN-CHG-001 v1.24 §10.6 — AnnualPlanScreen component tests (U07), verified
// against Artboards-U07-U08.dc.html.
//
// The preparation page's job is to say what still needs doing. Purchases lead
// and each names its own next work; Plan checks is three results, not eight;
// and the arithmetic behind a failing check stays where the correction is.
import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import AnnualPlanScreen from "./AnnualPlanScreen.vue";
import { BASE, READY } from "./ReservationAllocation.fixtures.js";
import {
	FINANCE_CONFIRMED,
	FINANCE_NOT_REQUESTED,
	FIT_OVER,
	FIT_WITHIN,
	METHOD_BLOCKED,
	OVER_BUDGET,
	WAITING_BUDGET,
	WAITING_SIGNATURE,
	planJourney,
} from "./guidance.fixtures.js";

const INFRASTRUCTURE = {
	plan_item_id: "PPI-MOH-2027-021",
	title: "National digital health infrastructure upgrade",
	quantity_number: "1",
	unit_label: "Programme",
	value_display: "KES 80,000,000",
	completion_display: "31 Aug 2027",
	current_work: "Choose a procurement method",
	sources: 1,
	route: ["procurement-plan-item", "PPI-MOH-2027-021"],
};

const LAPTOPS = {
	plan_item_id: "PPI-MOH-2027-033",
	title: "Clinical training and deployment laptops for digital health rollout",
	quantity_number: "250",
	unit_label: "Each",
	value_display: "KES 50,000,000",
	completion_display: "31 Dec 2027",
	current_work: "Review the required reserved allocation",
	sources: 2,
	route: ["procurement-plan-item", "PPI-MOH-2027-033"],
};

// PLN v1.27 — "Funding: Not yet checked" is retired; budget fit and Finance
// confirmation are their own facts (budget_fit / finance_confirmation).
const CHECKS = [
	{
		label: "Reserved procurement",
		result: "KES 139,494 more qualifying allocation required",
		kind: "critical",
		action: "Review reserved procurement",
		route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
	},
	{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null },
];

function plan(overrides = {}) {
	return {
		outcome: "OK",
		plan_reference: "PLN-MOH-2027-001",
		version_number: 1,
		version_status: "Draft",
		record_version: 3,
		mutable: true,
		is_successor: false,
		project_name: "",
		change_reason: "",
		header: { title: "Ministry of Health Annual Procurement Plan 2027/28", badge: "Draft" },
		plan_items: [INFRASTRUCTURE, LAPTOPS],
		unallocated_sources: [],
		plan_checks: CHECKS,
		changes: { is_initial: true },
		history: [{ title: "Digital Health · DPP-MOH-DHI-2027-001 accepted", meta: "Mercy Kilonzo · 27 Nov 2026, 14:00 EAT" }],
		summary: { reservation_allocation: BASE },
		submission_issues: [],
		can_request_funding: false,
		can_sign_and_submit: false,
		can_cancel_update: false,
		open_task: null,
		next_step: METHOD_BLOCKED,
		journey: planJourney("preparation", { blocked: true, holder: "Mercy Kilonzo" }),
		budget_fit: FIT_WITHIN,
		finance_confirmation: FINANCE_NOT_REQUESTED,
		...overrides,
	};
}

function make(props = {}) {
	return mount(AnnualPlanScreen, {
		props: { plan: plan(), selected: [], pending: false, errorSummary: "", ...props },
	});
}

describe("AnnualPlanScreen — U07 BASE", () => {
	it("leads with purchases, each naming its own next work", () => {
		const w = make();
		expect(w.find('[data-testid="ppl-title"]').text()).toBe("Prepare the annual procurement plan");
		const rows = w.findAll('[data-testid="ppl-purchase-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Choose a procurement method");
		expect(rows[1].text()).toContain("Review the required reserved allocation");
		// Not a generic readiness badge (§9.4).
		expect(w.text()).not.toContain("Complete readiness");
		expect(w.text()).not.toContain("Review required");
	});

	// A subtle per-row hint distinguishes an outstanding purchase from a
	// Ready one at a glance, using the same status-badge language every
	// other table in the app already uses for a row's state.
	it("marks each row's Current work with a status badge, not just plain text", () => {
		const w = make({
			plan: plan({ plan_items: [{ ...INFRASTRUCTURE, current_work: "Ready" }, LAPTOPS] }),
		});
		const rows = w.findAll('[data-testid="ppl-purchase-row"]');
		expect(rows[0].find(".kt-status").classes()).toContain("is-live");
		expect(rows[1].find(".kt-status").classes()).toContain("is-attention");
	});

	// A reader who cannot act on this plan — a Finance Confirmation Officer,
	// an Auditor — reaches the same read-only editor, but the row must not
	// promise a control the viewer does not have (found live 23 Sep 2026).
	it("names the row action View purchase for a reader who cannot act, Edit purchase for one who can", () => {
		const reader = make({ plan: plan({ mutable: false }) });
		expect(reader.find('[data-testid="ppl-purchase-action"]').text()).toBe("View purchase");

		const planner = make({ plan: plan({ mutable: true }) });
		expect(planner.find('[data-testid="ppl-purchase-action"]').text()).toBe("Edit purchase");
	});

	// PLN v1.27 D2: the reservation shortfall blocks only signature, so it is
	// a plain row carrying its correction; the page's one warning is the
	// next-step block, which names what stops the funding request.
	it("states the reservation shortfall as a plain row with its correction, not a second warning", () => {
		const w = make();
		const issue = w.find('[data-testid="ppl-check-issue"]');
		expect(issue.classes()).not.toContain("is-warning");
		expect(issue.text()).toContain("Reserved procurement");
		expect(issue.text()).toContain("KES 139,494 more qualifying allocation required");
		expect(w.find('[data-testid="ppl-check-action"]').text()).toBe("Review reserved procurement");
		expect(w.find('[data-testid="ppl-plan-checks-region"] .kt-notice.is-warning').exists()).toBe(false);
		expect(w.find(".kt-next-step-block").exists()).toBe(true);
		const checks = w.find('[data-testid="ppl-plan-checks"]');
		expect(checks.text()).toContain("Schedule");
		// The failing one is stated once, in its row — not twice.
		expect(checks.text()).not.toContain("Reserved procurement");
		expect(w.text()).not.toContain("Budget basis");
	});

	it("never says funding is not yet checked: budget fit is live and Finance confirmation is its own fact", () => {
		const w = make();
		expect(w.text()).not.toContain("Not yet checked");
		expect(w.find('[data-testid="ppl-budget-fit"]').text()).toContain("Budget fit, checked now");
		expect(w.find('[data-testid="ppl-budget-fit"]').text()).toContain("Within each approved budget line");
		expect(w.find('[data-testid="ppl-finance-confirmation"]').text()).toContain("Not requested");
		// Within budget, the per-line table waits behind "View budget lines".
		expect(w.find('[data-testid="ppl-budget-lines"]').element.tagName).toBe("DETAILS");
		expect(w.find('[data-testid="ppl-budget-fit-table"]').exists()).toBe(false);
	});

	it("omits the project-name field when blank, offering to add one instead", () => {
		const w = make();
		expect(w.find('[data-testid="ppl-project-name"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppl-add-project-name"]').exists()).toBe(true);
	});

	it("shows the project-name field when the plan has one", () => {
		const w = make({ plan: plan({ project_name: "National digital health rollout" }) });
		expect(w.find('[data-testid="ppl-project-name"]').exists()).toBe(true);
	});

	it("keeps changes and history closed by default", () => {
		const w = make();
		const history = w.find('[data-testid="ppl-history"]');
		expect(history.attributes("open")).toBeUndefined();
		expect(history.text()).toContain("This is the first version of the annual plan.");
	});

	// A dense paragraph per acceptance read as a wall of text with no reason
	// to (found live 23 Sep 2026); the same .kt-timeline used for history
	// elsewhere in the app (Departmental Needs, Strategy, Tenders) applies
	// here too.
	it("shows each departmental acceptance as a timeline entry, not a paragraph", () => {
		const w = make({
			plan: plan({
				history: [
					{ title: "Digital Health · DPP-MOH-DHI-2027-001 accepted", meta: "Mercy Kilonzo · 27 Nov 2026, 14:00 EAT" },
					{ title: "Human Resources Management and Development · DPP-MOH-HRMD-2027-001 accepted", meta: "Mercy Kilonzo · 27 Nov 2026, 14:05 EAT" },
				],
			}),
		});
		const timeline = w.find('[data-testid="ppl-history-timeline"]');
		const rows = timeline.findAll(".kt-timeline-row");
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Digital Health · DPP-MOH-DHI-2027-001 accepted");
		expect(rows[0].text()).toContain("Mercy Kilonzo · 27 Nov 2026, 14:00 EAT");
		// A connecting line between entries, none trailing the last one.
		expect(rows[0].find(".kt-timeline-line").exists()).toBe(true);
		expect(rows[1].find(".kt-timeline-line").exists()).toBe(false);
	});

	it("omits Send to Finance while a blocking check fails, and never shows Submit or Approve", () => {
		const w = make();
		expect(w.find('[data-testid="ppl-request-funding"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppl-save"]').exists()).toBe(true);
		const buttons = w.findAll("button").map((b) => b.text());
		expect(buttons.some((label) => /^(Submit|Approve)/.test(label))).toBe(false);
		// No Approval and publication section while the Draft is being prepared.
		expect(w.text()).not.toContain("Approval and publication");
	});

	it("offers Send to Finance once the checks allow it", () => {
		const w = make({ plan: plan({ can_request_funding: true }) });
		expect(w.find('[data-testid="ppl-request-funding"]').text()).toBe("Send to Finance for funding review");
	});

	// A plan whose purchases still have their own current work looks
	// finished (Plan checks can be all clear) with no visible next step
	// otherwise — Send to Finance is correctly absent, but nothing said why
	// (found live 23 Sep 2026). Stated right beside the table its own
	// "Current work" column is read from, not the footer — a sentence
	// there that just said "shown above" needed the reader to scroll back
	// up past three sections to see what it meant.
	it("says why nothing else is available, right beside the table current work names", () => {
		const w = make();
		const notice = w.find('[data-testid="ppl-incomplete-notice"]');
		expect(notice.text()).toContain("2 of the purchases above must show Ready in Current work");
		// Beside the table, inside the same region — not the footer.
		expect(notice.element.closest(".kt-region").querySelector('[data-testid="ppl-purchases"]')).toBeTruthy();
	});

	it("says nothing once every purchase is Ready, and still shows the table and its rows", () => {
		// `v-else` binds to the nearest preceding `v-if`; wrapping the table
		// and this notice in one `<template v-if="items.length">` matters,
		// not just cosmetically — without it, "No purchases have been added
		// yet." paired itself with the notice's own `v-if` instead of the
		// table's, so it appeared next to a fully populated, all-Ready table
		// (found live 23 Sep 2026, screenshotted moments after the notice
		// above was added).
		const w = make({
			plan: plan({ plan_items: [{ ...INFRASTRUCTURE, current_work: "Ready" }, { ...LAPTOPS, current_work: "Ready" }] }),
		});
		expect(w.find('[data-testid="ppl-incomplete-notice"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppl-purchases"]').exists()).toBe(true);
		expect(w.findAll('[data-testid="ppl-purchase-row"]')).toHaveLength(2);
		expect(w.find('[data-testid="ppl-purchases-empty"]').exists()).toBe(false);
	});
});

describe("AnnualPlanScreen — U07-UNALLOCATED and selection", () => {
	const SOURCE = {
		entry_id: "DPPE-MOH-DHI-2027-001",
		title: "National digital health infrastructure upgrade",
		source_label: "Accepted Need · NDS-MOH-2027-0001",
		department: "Digital Health",
		quantity_number: "1",
		unit_label: "Programme",
		amount_display: "KES 80,000,000",
	};

	it("shows the empty purchases state and the sources waiting to be added", () => {
		const w = make({ plan: plan({ plan_items: [], unallocated_sources: [SOURCE] }) });
		expect(w.find('[data-testid="ppl-purchases-empty"]').text()).toBe("No purchases have been added yet.");
		expect(w.findAll('[data-testid="ppl-unallocated-row"]')).toHaveLength(1);
	});

	it("holds Add selected requirements until at least one is ticked", async () => {
		const w = make({ plan: plan({ plan_items: [], unallocated_sources: [SOURCE] }) });
		expect(w.find('[data-testid="ppl-add-selected"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="ppl-select-hint"]').text()).toBe("Select at least one requirement.");

		const selected = make({ plan: plan({ plan_items: [], unallocated_sources: [SOURCE] }), selected: [SOURCE.entry_id] });
		expect(selected.find('[data-testid="ppl-add-selected"]').attributes("disabled")).toBeUndefined();
		expect(selected.find('[data-testid="ppl-select-hint"]').exists()).toBe(false);
	});

	it("emits the toggled source", async () => {
		const w = make({ plan: plan({ plan_items: [], unallocated_sources: [SOURCE] }) });
		await w.find('[data-testid="ppl-select-source"]').trigger("change");
		expect(w.emitted("toggle-source")[0]).toEqual([SOURCE.entry_id]);
	});

	it("says plainly when every requirement is already in a purchase", () => {
		const w = make();
		expect(w.find('[data-testid="ppl-all-allocated"]').text()).toBe(
			"All 3 departmental requirements are included in the 2 purchases above.",
		);
		expect(w.find('[data-testid="ppl-add-selected"]').exists()).toBe(false);
	});
});

describe("AnnualPlanScreen — U07-UPDATE", () => {
	it("names itself an update, shows the current version and asks why", () => {
		const w = make({
			plan: plan({
				is_successor: true,
				version_number: 2,
				current_version_number: 1,
				can_cancel_update: true,
			}),
		});
		expect(w.find('[data-testid="ppl-title"]').text()).toBe("Prepare plan update");
		expect(w.find('[data-testid="ppl-context"]').text()).toContain("Draft update");
		expect(w.find('[data-testid="ppl-context"]').text()).toContain("Version 1");
		expect(w.find('[data-testid="ppl-change-reason"]').exists()).toBe(true);
		expect(w.find('[data-testid="ppl-cancel-update"]').text()).toBe("Cancel plan update");
	});
});

describe("AnnualPlanScreen — U07-FINANCE-COMPLETE", () => {
	const financeComplete = (overrides = {}) =>
		plan({
			can_request_funding: false,
			plan_checks: [
				{ label: "Reserved procurement", result: "Required allocation met", kind: "live", route: null },
				{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null },
			],
			next_step: WAITING_SIGNATURE,
			journey: planJourney("signature", { holder: "Charles Mutiso (Head of Procurement Function)" }),
			finance_confirmation: FINANCE_CONFIRMED,
			summary: { reservation_allocation: READY },
			...overrides,
		});

	// KT-STD-001 v1.8 §3B.3 — the next-step line names the person and how
	// long it has waited, in the page head; it replaces the old Approval
	// region and its "Responsible person" label.
	it("names who it is waiting on, and since when, in the page head rather than an Approval region", () => {
		const w = make({ plan: financeComplete() });
		const line = w.find('[data-testid="ppl-next-step-line"] .kt-next-step');
		expect(line.exists()).toBe(true);
		expect(line.attributes("data-kind")).toBe("waiting");
		expect(line.text()).toContain("Waiting for Charles Mutiso (Head of Procurement Function) to sign and submit");
		expect(line.text()).toContain("since 4 Dec 2026, 10:00 EAT");
		expect(w.find(".kt-page-head").element.contains(line.element)).toBe(true);
		expect(w.find('[data-testid="ppl-waiting-on"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Responsible person");
		// The Planner gets no approval or handover action of their own.
		expect(w.find('[data-testid="ppl-sign-submit"]').exists()).toBe(false);
		expect(w.find(".kt-next-step-block").exists()).toBe(false);
	});

	it("marks Signature as the current stage of the plan's journey", () => {
		const w = make({ plan: financeComplete() });
		const current = w.find('[data-testid="ppl-journey"] .kt-journey-stage.is-current');
		expect(current.text()).toContain("Signature");
		expect(w.findAll('[data-testid="ppl-journey"] .kt-journey-stage.is-done')).toHaveLength(2);
	});

	it("shows who confirmed funding and when, beside the live budget fit", () => {
		const w = make({ plan: financeComplete() });
		const checks = w.find('[data-testid="ppl-plan-checks"]');
		expect(checks.text()).toContain("Confirmed");
		expect(checks.text()).toContain("Josphat Mwangi");
		expect(checks.text()).toContain("4 Dec 2026, 10:00 EAT");
	});

	it("offers Sign and submit only to the actor who holds it", () => {
		const w = make({ plan: plan({ can_sign_and_submit: true }) });
		expect(w.find('[data-testid="ppl-sign-submit"]').text()).toBe("Sign and submit Annual Plan");
	});
});

describe("AnnualPlanScreen — a reader who cannot change the plan", () => {
	it("is offered no way to form purchases, not a disabled one", () => {
		const w = make({
			plan: plan({
				mutable: false,
				can_act: false,
				unallocated_sources: [
					{ entry_id: "DPP-MOH-DH-2027-004", dpp_entry: "DPE-0004", title: "A requirement not yet in a purchase", department: "Digital Health", quantity_number: "1", unit_label: "Programme", amount_display: "KES 10,000,000", source_label: "Accepted Need · NDS-MOH-2027-0009" },
				],
			}),
		});
		// §10.6 — the requirements are still readable; only the controls go.
		expect(w.find('[data-testid="ppl-unallocated"]').exists()).toBe(true);
		expect(w.find('[data-testid="ppl-select-source"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppl-add-selected"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppl-save"]').exists()).toBe(false);
	});
});


// PLN v1.25 — one plan-level Reservation allocation block, placed as the U07
// boards draw it. Not met, it follows its own warning, above the quiet
// checks (U07 base); met, it follows them (U07-FINANCE-COMPLETE). Either way
// the reserved-procurement result leaves the quiet-checks group, because the
// block states it.
describe("AnnualPlanScreen — the Reservation allocation block", () => {
	const order = (w) => {
		const region = w.find('[data-testid="ppl-plan-checks-group"]').element.parentElement;
		// The block sits in a focusable host (the "Review reserved
		// procurement" fix scrolls to it), so read the host's child.
		return [...region.children].map((el) => el.dataset.testid || el.firstElementChild?.dataset.testid).filter(Boolean);
	};

	it("follows the warning and precedes the quiet checks while the allocation is not met", () => {
		const w = make();
		expect(order(w)).toEqual(["ppl-check-issue", "reservation-allocation", "ppl-plan-checks-group"]);
		expect(w.find('[data-testid="reservation-status"]').text()).toBe("Required allocation not met");
		expect(w.find('[data-testid="reservation-details"]').element.tagName).toBe("DETAILS");
	});

	it("follows the quiet checks once the allocation is met, and the met row is not repeated", () => {
		const checks = [
			{ label: "Reserved procurement", result: "Required allocation met", kind: "live", route: null },
			{ label: "Schedule", result: "Both purchases meet their departmental deadlines", kind: "live", route: null },
		];
		const w = make({ plan: plan({ plan_checks: checks, summary: { reservation_allocation: READY } }) });
		expect(order(w)).toEqual(["ppl-plan-checks-group", "reservation-allocation"]);
		expect(w.find('[data-testid="ppl-plan-checks"]').text()).not.toContain("Reserved procurement");
		expect(w.find('[data-testid="reservation-result"]').text()).toContain("38.46%");
	});

	it("says nothing at all where no reserved-procurement target is published", () => {
		const w = make({ plan: plan({ summary: { reservation_allocation: null } }) });
		expect(w.find('[data-testid="reservation-allocation"]').exists()).toBe(false);
	});
});

// Each correction used to earn the next refusal: the server computed the
// whole blocker list and raised only the first (found live 23 Sep 2026).
describe("AnnualPlanScreen — what still stands in the way of submission", () => {
	const ISSUES = [
		"Reserved procurement is below the required amount. Review the shortfall shown. Required KES 139,494 (30% of KES 464,980 planned), reserved KES 0, short by KES 139,494.",
		"Choose a strategic objective currently available for this plan. (PPI-MOH-2027-033)",
	];

	it("names every outstanding issue at once, with the count", () => {
		const w = make({ plan: plan({ submission_issues: ISSUES }) });
		const block = w.find('[data-testid="ppl-submission-issues"]');
		expect(block.text()).toContain("2 issues must be resolved before this plan can be submitted");
		const rows = w.findAll('[data-testid="ppl-submission-issue"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("KES 139,494");
		expect(rows[1].text()).toContain("Choose a strategic objective");
	});

	it("counts one issue in the singular", () => {
		const w = make({ plan: plan({ submission_issues: [ISSUES[0]] }) });
		expect(w.find('[data-testid="ppl-submission-issues"]').text()).toContain(
			"1 issue must be resolved before this plan can be submitted",
		);
	});

	it("is absent when nothing stands in the way", () => {
		expect(make().find('[data-testid="ppl-submission-issues"]').exists()).toBe(false);
	});
});

// Structure, against Artboards-U07-U08.dc.html. Found live 24 Sep 2026: the
// page read as a flat wall of labelled text once the Planner had nothing left
// to do on it. Three structures the board draws had been dropped — the group
// rule around Plan checks, the width bound on its rows, and Approval's own
// region and notice.
describe("AnnualPlanScreen — the structures the board draws", () => {
	it("binds Plan checks inside a group, as the board does", () => {
		const group = make().find('[data-testid="ppl-plan-checks-group"]');
		expect(group.exists()).toBe(true);
		expect(group.classes()).toContain("kt-group");
		expect(group.find('[data-testid="ppl-plan-checks"]').exists()).toBe(true);
	});

	it("draws no Approval region: the next-step line replaced it", () => {
		const w = make({ plan: plan({ next_step: WAITING_SIGNATURE }) });
		expect(w.find('[data-testid="ppl-waiting-on"]').exists()).toBe(false);
		expect(w.findAll("h2").map((h) => h.text())).not.toContain("Approval");
	});
});

// The board's disclosure head carries a title row and a chevron; the port had
// only a bare span, so the section read as an orphaned small-caps heading over
// empty space with nothing saying it opened (found live 24 Sep 2026).
describe("AnnualPlanScreen — Changes and history", () => {
	it("says it opens", () => {
		const head = make().find('[data-testid="ppl-history"] .kt-disclosure-head');
		expect(head.find(".kt-disclosure-title-row").text()).toBe("Changes and history");
		expect(head.find(".kt-disclosure-chevron").exists()).toBe(true);
	});
});

// PLN v1.27 §10.6 U07-UPDATE-OVER-BUDGET / U07-WAITING-BUDGET-REVISION — the
// next-step block names what stops the funding request and carries the fixes;
// the screen maps each fix to its own handler and computes no wording.
describe("AnnualPlanScreen — the next step and its fixes", () => {
	const overBudget = (overrides = {}) =>
		plan({ is_successor: true, next_step: OVER_BUDGET, budget_fit: FIT_OVER, ...overrides });

	it("names the over-budget line in the blocked block, and opens the line comparison", () => {
		const w = make({ plan: overBudget() });
		const block = w.find('[data-testid="ppl-next-step-block"] .kt-next-step-block');
		expect(block.text()).toContain("Over budget by KES 2,000,000 on Digital health workforce development");
		expect(block.text()).toContain("cannot be lowered in the plan");
		expect(w.find('[data-testid="ppl-budget-fit-over"]').text()).toContain("Over by KES 2,000,000 on one budget line");
		expect(w.find('[data-testid="ppl-budget-fit-table"] .pln-fit-over-cell').text()).toBe("Over by KES 2,000,000");
		expect(w.find('[data-testid="ppl-budget-lines"]').exists()).toBe(false);
		// The head line is reserved for Your turn / Waiting / Done.
		expect(w.find('[data-testid="ppl-next-step-line"] .kt-next-step').exists()).toBe(false);
	});

	it("hands Request budget revision to the page as a command, with its budget line", async () => {
		const w = make({ plan: overBudget() });
		await w.find('[data-fix="request_budget_revision"]').trigger("click");
		const [fix] = w.emitted("guidance-command")[0];
		expect(fix.fix_id).toBe("request_budget_revision");
		expect(fix.target).toEqual({ budget_line: "MOH-BL-HWD-2027" });
		expect(w.find('[data-fix="request_budget_revision"]').classes()).toContain("btn-primary");
	});

	it("hands Request departmental plan update to the page as a command, with the line and the department", async () => {
		// Owner decision 26 Sep 2026: the departmental correction route replaces
		// "Reduce a purchase", which offered an edit the purchase editor locks.
		const w = make({ plan: overBudget() });
		expect(w.find('[data-fix="reduce_purchase"]').exists()).toBe(false);
		await w.find('[data-fix="request_departmental_update"]').trigger("click");
		const [fix] = w.emitted("guidance-command")[0];
		expect(fix.fix_id).toBe("request_departmental_update");
		expect(fix.target).toEqual({ budget_line: "MOH-BL-HWD-2027", organisation_unit: "OU-HRMD" });
		expect(w.find('[data-fix="request_departmental_update"]').text()).toBe("Request departmental plan update from Human Resources Management and Development");
		expect(w.find(".kt-next-step-block").text()).toContain("Requirements on this line");
	});

	it("opens the purchase when the fix is Choose a procurement method", async () => {
		const w = make();
		await w.find('[data-fix="choose_method"]').trigger("click");
		expect(w.emitted("navigate")[0]).toEqual([["procurement-plan-item", "PPI-MOH-2027-021"]]);
	});

	it("holds every fix while a command is in flight", () => {
		const w = make({ plan: overBudget(), pending: true });
		expect(w.find('[data-fix="request_budget_revision"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-fix="request_departmental_update"]').attributes("disabled")).toBeDefined();
	});

	it("says it is waiting on the Budget Officer once the revision is requested, with no fix to repeat", () => {
		const w = make({ plan: overBudget({ next_step: WAITING_BUDGET }) });
		const line = w.find('[data-testid="ppl-next-step-line"] .kt-next-step');
		expect(line.text()).toContain("Waiting for Josphat Mwangi (Budget Officer) to revise the budget line");
		expect(line.text()).toContain("since 15 Dec 2026, 10:00 EAT");
		expect(w.find('[data-fix="request_budget_revision"]').exists()).toBe(false);
		expect(w.find(".kt-next-step-block").exists()).toBe(false);
	});

	it("redraws the next step in place when the server answer changes", async () => {
		const w = make({ plan: overBudget() });
		expect(w.find(".kt-next-step-block").exists()).toBe(true);
		await w.setProps({ plan: overBudget({ next_step: WAITING_BUDGET }) });
		await new Promise((resolve) => setTimeout(resolve));
		expect(w.find(".kt-next-step-block").exists()).toBe(false);
		expect(w.find('[data-testid="ppl-next-step-line"]').text()).toContain("Waiting for Josphat Mwangi");
	});

	it("draws nothing at all where the server supplies no next step", () => {
		const w = make({ plan: plan({ next_step: null, journey: null }) });
		expect(w.find(".kt-next-step").exists()).toBe(false);
		expect(w.find(".kt-next-step-block").exists()).toBe(false);
		expect(w.find(".kt-journey").exists()).toBe(false);
	});
});
