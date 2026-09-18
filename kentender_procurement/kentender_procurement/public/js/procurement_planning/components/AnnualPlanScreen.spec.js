// PLN-CHG-001 v1.23 §10.6 — AnnualPlanScreen component tests (U07).
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
		result: "KES 48,000,000 more qualifying allocation required",
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
		history_lines: ["Digital Health acceptance: Mercy Kilonzo, 27 Nov 2026, 14:00 EAT"],
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

	it("shows exactly three plan checks, with the failing one linking to its correction", () => {
		const w = make();
		const checks = w.find('[data-testid="ppl-plan-checks"]');
		expect(checks.text()).toContain("Funding");
		expect(checks.text()).toContain("Reserved procurement");
		expect(checks.text()).toContain("Schedule");
		expect(checks.text()).toContain("KES 48,000,000 more qualifying allocation required");
		expect(w.find('[data-testid="ppl-check-action"]').text()).toBe("Review reserved procurement");
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

