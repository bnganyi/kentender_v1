// PLN-CHG-001 v1.24 §10.6 — AnnualPlanScreen component tests (U07), verified
// against Artboards-U07-U08.dc.html.
//
// The preparation page's job is to say what still needs doing. Purchases lead
// and each names its own next work; Plan checks is three results, not eight;
// and the arithmetic behind a failing check stays where the correction is.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AnnualPlanScreen from "./AnnualPlanScreen.vue";

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

const CHECKS = [
	{ label: "Funding", result: "Not yet checked", kind: "neutral", route: null },
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
		summary: {
			reservation_summary: [
				{ label: "Eligible planned procurement", value: "KES 464,980" },
				{ label: "Required allocation at 30%", value: "KES 139,494" },
				{ label: "Reserved so far", value: "KES 0" },
				{ label: "Still required", value: "KES 139,494" },
				{ label: "Counting towards it", value: "No purchase yet" },
			],
		},
		submission_issues: [],
		can_request_funding: false,
		can_sign_and_submit: false,
		can_cancel_update: false,
		open_task: null,
		waiting_on: { notice: "", people: [], unassigned: "" },
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

	it("makes a failing check the dominant issue and keeps the passing ones quiet", () => {
		// The board draws a failing check as its own warning notice carrying
		// the correction, and the passing ones as quiet facts below. Built as
		// one flat row of facts, a KES 139,494 shortfall read no louder than
		// "all purchases meet their deadlines" (found live 24 Sep 2026).
		const w = make();
		const issue = w.find('[data-testid="ppl-check-issue"]');
		expect(issue.classes()).toContain("is-warning");
		expect(issue.text()).toContain("Reserved procurement");
		expect(issue.text()).toContain("KES 139,494 more qualifying allocation required");
		expect(w.find('[data-testid="ppl-check-action"]').text()).toBe("Review reserved procurement");
		const checks = w.find('[data-testid="ppl-plan-checks"]');
		expect(checks.text()).toContain("Funding");
		expect(checks.text()).toContain("Schedule");
		// The failing one is stated once, in the notice — not twice.
		expect(checks.text()).not.toContain("Reserved procurement");
		// PLN22-AC-006: the required/qualifying/shortfall arithmetic is not
		// repeated here.
		expect(w.text()).not.toContain("Planned qualifying allocation");
		expect(w.text()).not.toContain("Budget basis");
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
		expect(w.text()).not.toContain("Approve");
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
	it("names the responsible person rather than offering the Planner a handover control", () => {
		const w = make({
			plan: plan({
				can_request_funding: false,
				plan_checks: [
					{ label: "Funding", result: "Within each approved budget line", kind: "live", route: null },
					{ label: "Reserved procurement", result: "Required allocation met", kind: "live", route: null },
					{ label: "Schedule", result: "All purchases meet their departmental deadlines", kind: "live", route: null },
				],
				waiting_on: {
					notice: "Ready for the Head of Procurement Function to sign and submit",
					people: ["Charles Mutiso"],
					unassigned: "",
				},
			}),
		});
		// §10.6 — the notice and the person are separately labelled facts.
		const waiting = w.find('[data-testid="ppl-waiting-on"]');
		expect(waiting.text()).toContain("Ready for the Head of Procurement Function to sign and submit");
		expect(waiting.text()).toContain("Responsible person");
		expect(w.find('[data-testid="ppl-waiting-on-person"]').text()).toBe("Charles Mutiso");
		// The Planner gets no approval or handover action of their own.
		expect(w.find('[data-testid="ppl-sign-submit"]').exists()).toBe(false);
	});

	it("U07-FINANCE-COMPLETE: several holders are a list of people, not a slash-run", () => {
		const w = make({
			plan: plan({
				waiting_on: {
					notice: "Ready for the Head of Procurement Function to sign and submit",
					people: ["Ada Kimani", "Charles Mutiso"],
					unassigned: "",
				},
			}),
		});
		expect(w.find('[data-testid="ppl-waiting-on"]').text()).toContain("Responsible people");
		expect(w.find('[data-testid="ppl-waiting-on-person"]').text()).toBe("Ada Kimani, Charles Mutiso");
		expect(w.find('[data-testid="ppl-waiting-on"]').text()).not.toContain(" / ");
	});

	// The artboard (U07-FINANCE-COMPLETE) draws the Approval notice, then the
	// final Save draft button beneath a divider — in that order. Save draft
	// used to render first, so it read as the page's last word even once
	// nothing further was the Planner's to do (found live 23 Sep 2026).
	it("names who this is waiting on before the final Save draft action, not after", () => {
		const w = make({
			plan: plan({
				waiting_on: { notice: "Ready for the Head of Procurement Function to sign and submit", people: ["Charles Mutiso"], unassigned: "" },
			}),
		});
		const positions = [...w.element.querySelectorAll('[data-testid="ppl-waiting-on"], [data-testid="ppl-footer"]')].map((el) => el.getAttribute("data-testid"));
		expect(positions).toEqual(["ppl-waiting-on", "ppl-footer"]);
	});

	it("U07-FINANCE-COMPLETE: no holder names the configuration issue, never an assignee (§6.5)", () => {
		const w = make({
			plan: plan({
				waiting_on: {
					notice: "Ready for the Head of Procurement Function to sign and submit",
					people: [],
					unassigned: "No one currently holds that responsibility — ask your KenTender administrator.",
				},
			}),
		});
		expect(w.find('[data-testid="ppl-waiting-on-person"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppl-waiting-on-unassigned"]').text()).toContain("ask your KenTender administrator");
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


// The reservation figures used to exist only inside a refusal at Sign and
// submit, as raw unformatted numbers with no statement of what they were a
// share of — "Required 48000000.00, planned 0.00" against a plan of KES
// 464,980 (found live 23 Sep 2026). The working belongs on the screen where
// the work is done.
describe("AnnualPlanScreen — the reserved-procurement working", () => {
	it("shows what the target is a share of, what it comes to, and what is left", () => {
		const summary = make().find('[data-testid="ppl-reservation-summary"]');
		expect(summary.exists()).toBe(true);
		expect(summary.text()).toContain("Eligible planned procurement");
		expect(summary.text()).toContain("KES 464,980");
		expect(summary.text()).toContain("Required allocation at 30%");
		expect(summary.text()).toContain("KES 139,494");
		expect(summary.text()).toContain("Reserved so far");
		expect(summary.text()).toContain("Counting towards it");
	});

	it("says nothing at all where no reserved-procurement target is published", () => {
		const w = make({ plan: plan({ summary: { reservation_summary: [] } }) });
		expect(w.find('[data-testid="ppl-reservation-summary"]').exists()).toBe(false);
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
		// Both rows live inside the one rule, so the reserved-procurement
		// working reads as part of the checks rather than a second loose band.
		expect(group.find('[data-testid="ppl-plan-checks"]').exists()).toBe(true);
		expect(group.find('[data-testid="ppl-reservation-summary"]').exists()).toBe(true);
	});

	it("gives Approval its own region and notice rather than loose labels", () => {
		const w = make({
			plan: plan({ waiting_on: { notice: "Ready for the Head of Procurement Function to sign and submit", people: ["Charles Mutiso"], unassigned: "" } }),
		});
		const region = w.find('[data-testid="ppl-waiting-on"]');
		expect(region.classes()).toContain("kt-region");
		expect(region.classes()).toContain("is-secondary");
		expect(region.find("h2").text()).toBe("Approval");
		expect(region.find(".kt-notice").exists()).toBe(true);
		expect(region.text()).toContain("Ready for the Head of Procurement Function to sign and submit");
		expect(w.find('[data-testid="ppl-waiting-on-person"]').text()).toContain("Charles Mutiso");
	});

	it("names several responsible people without inventing a delimiter row", () => {
		const w = make({
			plan: plan({ waiting_on: { notice: "Ready to sign and submit", people: ["Charles Mutiso", "Asha Njeri"], unassigned: "" } }),
		});
		expect(w.find('[data-testid="ppl-waiting-on-person"]').text()).toContain("Charles Mutiso, Asha Njeri");
		expect(w.find('[data-testid="ppl-waiting-on"]').text()).toContain("Responsible people");
	});

	it("still says who is unassigned where nobody holds it", () => {
		const w = make({
			plan: plan({ waiting_on: { notice: "Waiting", people: [], unassigned: "No Head of Procurement Function is assigned" } }),
		});
		expect(w.find('[data-testid="ppl-waiting-on-unassigned"]').text()).toBe("No Head of Procurement Function is assigned");
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
