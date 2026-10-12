// PLN-CHG-001 v1.23 §10.4 — DppPlanScreen component tests (U02–U05).
//
// The same page serves the Author and the Head of Department. What differs is
// the claim it makes: the Author is entering a plan and is told who submits
// it; the HoD is reviewing a complete one and certifies it here. These tests
// pin that difference, and pin that an excluded requirement stays visible with
// its reason rather than disappearing from the department's own plan.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import DppPlanScreen from "./DppPlanScreen.vue";
import { AUTHOR_DRAFT_TURN, CLOSED_BLOCKED, CORRECTION_TURN, HOD_TURN, dppJourney } from "./guidance.fixtures.js";

const INFRASTRUCTURE = {
	entry_id: "DPPE-MOH-DHI-2027-001",
	source_origin: "Accepted Departmental Need",
	title: "National digital health infrastructure upgrade",
	reference_line: "NDS-MOH-2027-0001 · Revision 1",
	quantity_number: "1",
	unit_label: "Programme",
	required_by_display: "31 Aug 2027",
	amount_display: "Not entered",
	status: "Funding details needed",
	status_kind: "attention",
	disposition: "Proceeding",
	not_proceeding_reason: "",
	action: "Enter funding details",
	issues: [],
};

const LAPTOPS = {
	entry_id: "DPPE-MOH-DHI-2027-002",
	source_origin: "Accepted Departmental Need",
	title: "Clinical deployment laptops for digital health rollout",
	reference_line: "NDS-MOH-2027-0004 · Revision 1",
	quantity_number: "150",
	unit_label: "Each",
	required_by_display: "31 Dec 2027",
	amount_display: "KES 30,000,000",
	status: "Included",
	status_kind: "live",
	disposition: "Proceeding",
	not_proceeding_reason: "",
	action: "Review details",
	issues: [],
};

function plan(overrides = {}) {
	return {
		outcome: "OK",
		access: "author",
		mutable: true,
		can_submit: false,
		can_create_update: false,
		is_correction: false,
		header: { badge: "Draft", badge_kind: "draft" },
		context: {
			department: "DHI — Digital Health",
			department_name: "Digital Health",
			financial_year: "FY 2027/28",
			window: { state: "Open", display: "Open" },
		},
		entries: [INFRASTRUCTURE, LAPTOPS],
		included_cost_display: "KES 30,000,000",
		certification: { show: false },
		submit_hint: "",
		open_task: null,
		next_step: AUTHOR_DRAFT_TURN,
		journey: dppJourney("preparation", { holder: "Grace Wanjiku", reduced: true }),
		...overrides,
	};
}

function make(props = {}) {
	return mount(DppPlanScreen, {
		props: { plan: plan(), pending: false, certified: false, errorSummary: "", ...props },
	});
}

describe("DppPlanScreen — U02-AUTHOR-DRAFT", () => {
	it("says whose turn it is in the head and where the plan stands in one reduced line, instead of a Status cell", () => {
		const w = make();
		expect(w.find(".kt-page-head .kt-next-step").text()).toBe("Your turn Enter funding details for 1 requirement");
		expect(w.find(".kt-journey.is-reduced").text()).toBe("Stage 1 of 4: Preparation — Grace Wanjiku");
		expect(w.find('[data-testid="pln-dpp-context"]').text()).not.toContain("Status");
	});

	it("uses the Author's own heading and summary labels", () => {
		const w = make();
		expect(w.find('[data-testid="pln-dpp-title"]').text()).toBe("Your departmental procurement plan");
		const summary = w.find('[data-testid="pln-dpp-summary"]').text();
		expect(summary).toContain("Requirements");
		// "entered so far" is the honest claim: no complete total exists yet.
		expect(summary).toContain("Cost entered so far");
		expect(summary).toContain("Requirements needing details");
		expect(summary).not.toContain("Included cost");
	});

	it("renders each requirement with its reference beneath the name", () => {
		const w = make();
		const rows = w.findAll('[data-testid="pln-dpp-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("National digital health infrastructure upgrade");
		expect(rows[0].text()).toContain("NDS-MOH-2027-0001 · Revision 1");
		expect(rows[0].text()).toContain("Not entered");
		expect(rows[0].text()).toContain("Funding details needed");
		expect(rows[1].text()).toContain("KES 30,000,000");
	});

	it("has separate Quantity and Unit columns", () => {
		const w = make();
		const headers = w.findAll('[data-testid="pln-dpp-table"] th').map((th) => th.text());
		expect(headers).toEqual(["Requirement", "Quantity", "Unit", "Required by", "Estimated cost", "Status", "Action"]);
	});

	it("tells the Author who submits, and shows no certification or submit control", () => {
		const w = make({ plan: plan({ submit_hint: "Your Head of Department must review and submit this plan." }) });
		expect(w.find('[data-testid="pln-dpp-submit-hint"]').text()).toBe(
			"Your Head of Department must review and submit this plan.",
		);
		expect(w.find('[data-testid="pln-dpp-certification"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-dpp-submit"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-dpp-save"]').exists()).toBe(true);
	});
});

describe("DppPlanScreen — U03 exclusions", () => {
	it("keeps an excluded requirement in the table with its full reason visible", () => {
		const excluded = {
			...INFRASTRUCTURE,
			amount_display: "Not applicable",
			status: "Not included this year",
			status_kind: "muted",
			disposition: "Not proceeding",
			not_proceeding_reason: "The department will pursue this requirement in a later annual planning cycle.",
			action: "Include in this year's departmental plan",
		};
		const w = make({ plan: plan({ entries: [excluded, LAPTOPS] }) });
		expect(w.findAll('[data-testid="pln-dpp-row"]')).toHaveLength(2);
		const reason = w.find('[data-testid="pln-dpp-exclusion-reason"]');
		// Always visible: the reason is the content of the exclusion, not
		// supporting detail behind a disclosure.
		expect(reason.text()).toContain("The department will pursue this requirement in a later annual planning cycle.");
		expect(w.findAll('[data-testid="pln-dpp-row"]')[0].text()).toContain("Not applicable");
	});

	it("emits restore for an excluded row's include action, not the entry editor", () => {
		const excluded = {
			...INFRASTRUCTURE,
			disposition: "Not proceeding",
			not_proceeding_reason: "Deferred to a later cycle for the reasons recorded here.",
			action: "Include in this year's departmental plan",
		};
		const w = make({ plan: plan({ entries: [excluded] }) });
		w.find('[data-testid="pln-dpp-row-action"]').trigger("click");
		expect(w.emitted("restore-entry")).toBeTruthy();
		expect(w.emitted("open-entry")).toBeFalsy();
	});
});

describe("DppPlanScreen — U03-FUNDING", () => {
	it("names the open row plainly instead of repeating its live action link", () => {
		const w = make({ fundingEntryId: INFRASTRUCTURE.entry_id });
		const openRow = w.findAll('[data-testid="pln-dpp-row"]')[0];
		expect(openRow.find('[data-testid="pln-dpp-row-editing"]').text()).toBe("Editing");
		expect(openRow.find('[data-testid="pln-dpp-row-action"]').exists()).toBe(false);
		// The other row, whose panel is not open, keeps its own action link.
		const otherRow = w.findAll('[data-testid="pln-dpp-row"]')[1];
		expect(otherRow.find('[data-testid="pln-dpp-row-editing"]').exists()).toBe(false);
		expect(otherRow.find('[data-testid="pln-dpp-row-action"]').text()).toBe("Review details");
	});
});

describe("DppPlanScreen — U05-HOD", () => {
	function hod(extra = {}) {
		return make({
			plan: plan({
				access: "hod",
				can_submit: true,
				included_cost_display: "KES 110,000,000",
				entries: [
					{ ...INFRASTRUCTURE, amount_display: "KES 80,000,000", status: "Included", status_kind: "live", action: "View details" },
					{ ...LAPTOPS, action: "View details" },
				],
				certification: {
					show: true,
					text: "I certify that this plan records Digital Health's procurement requirements for FY 2027/28.",
					checkbox_label: "I confirm this certification",
				},
				next_step: HOD_TURN,
				journey: dppJourney("certification", { holder: "Julia Njeri" }),
				...extra,
			}),
		});
	}

	it("asks the Head of Department to certify, keeps the Status cell and the full tracker", () => {
		const w = hod();
		expect(w.find(".kt-page-head .kt-next-step").text()).toBe("Your turn Certify and submit the departmental plan");
		expect(w.find(".kt-journey").classes()).not.toContain("is-reduced");
		expect(w.find(".kt-journey-stage.is-current").text()).toContain("Certification");
		expect(w.find('[data-testid="pln-dpp-context"]').text()).toContain("Status");
	});

	it("names an accepted plan instead of asking for a review and submission (owner instruction 28 Sep 2026)", () => {
		const w = make({ plan: plan({ access: "hod", mutable: false, current_state: "Accepted", version: { status: "Accepted" } }) });
		expect(w.find('[data-testid="pln-dpp-title"]').text()).toBe("Digital Health's departmental plan");
		expect(w.find(".kt-page-desc").text()).toBe("Accepted by Procurement for this financial year.");
	});

	it("names a submitted plan as with Procurement", () => {
		const w = make({ plan: plan({ access: "author", mutable: false, current_state: "Submitted", version: { status: "Submitted" } }) });
		expect(w.find('[data-testid="pln-dpp-title"]').text()).toBe("Digital Health's departmental plan");
		expect(w.find(".kt-page-desc").text()).toBe("Submitted to Procurement for review. It cannot be changed while Procurement reviews it.");
	});

	it("reads as a complete review of the department's plan", () => {
		const w = hod();
		expect(w.find('[data-testid="pln-dpp-title"]').text()).toBe("Review Digital Health's departmental plan");
		const summary = w.find('[data-testid="pln-dpp-summary"]').text();
		expect(summary).toContain("Included cost");
		expect(summary).toContain("KES 110,000,000");
		expect(summary).toContain("Excluded requirements");
	});

	it("certifies on the same page and disables submit until confirmed", () => {
		const w = hod();
		expect(w.find('[data-testid="pln-dpp-certification"]').exists()).toBe(true);
		const submit = w.find('[data-testid="pln-dpp-submit"]');
		expect(submit.text()).toBe("Submit departmental plan");
		expect(submit.attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pln-dpp-certify-hint"]').text()).toBe("Confirm the certification to submit this plan.");
	});

	it("enables submit once the certification is confirmed", () => {
		const w = make({
			certified: true,
			plan: plan({
				access: "hod",
				can_submit: true,
				certification: { show: true, text: "I certify…", checkbox_label: "I confirm this certification" },
			}),
		});
		expect(w.find('[data-testid="pln-dpp-submit"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="pln-dpp-certify-hint"]').exists()).toBe(false);
	});
});

describe("DppPlanScreen — U05-CORRECTION and U02-CLOSED", () => {
	it("leads with the correction notice, shows the comment beside its row, and resubmits", () => {
		const w = make({
			certified: true,
			plan: plan({
				access: "hod",
				can_submit: true,
				is_correction: true,
				next_step: CORRECTION_TURN,
				journey: dppJourney("preparation"),
				returned_submission_number: 1,
				candidate_submission_number: 2,
				certification: { show: true, text: "I certify…", checkbox_label: "I confirm this certification" },
				entries: [
					{
						...LAPTOPS,
						issues: [{ problem: "", correction: "Explain how the KES 30,000,000 estimate for the deployment laptops was calculated, or correct the amount." }],
					},
				],
			}),
		});
		// PLN v1.27 — the next-step line replaces the "Your plan needs a
		// correction" notice; Procurement's comment stays beside its row.
		expect(w.find('[data-testid="pln-dpp-correction-notice"]').exists()).toBe(false);
		expect(w.find(".kt-page-head .kt-next-step").text()).toBe("Your turn Correct and resubmit the departmental plan");
		expect(w.find(".kt-journey-stage.is-current").text()).toContain("Preparation");
		// Returned submission 1, correction submission 2 — two distinct facts,
		// each separately labelled (§10.4's own context-row convention).
		const context = w.find('[data-testid="pln-dpp-context"]').text();
		expect(context).toContain("Returned submission");
		expect(context).toContain("Correction submission");
		const issue = w.find('[data-testid="pln-dpp-issue"]');
		// The artboard's own display label for a returned comment shown back
		// to the department — "What needs to change?" is the return dialog's
		// *input* label, a different string for a different place.
		expect(issue.text()).toContain("Procurement comment");
		expect(issue.text()).toContain(
			"Explain how the KES 30,000,000 estimate for the deployment laptops was calculated",
		);
		expect(w.find('[data-testid="pln-dpp-submit"]').text()).toBe("Resubmit departmental plan");
		// New requirements belong in the next update, and there is no add
		// action here to suggest otherwise.
		expect(w.find('[data-testid="pln-dpp-next-update"]').text()).toContain(
			"Finish this correction first. New requirements belong in the next update.",
		);
	});

	it("keeps a closed-intake draft editable while saying, once, why it cannot be submitted", () => {
		const w = make({
			plan: plan({
				context: { ...plan().context, window: { state: "Closed", display: "Closed" } },
				next_step: CLOSED_BLOCKED,
				journey: dppJourney("preparation", { holder: "Grace Wanjiku" }),
				missing_setting: { title: "Departmental plan submissions are closed", items: [] },
			}),
		});
		// PLN v1.27 — the blocked next-step block replaces the footer sentence
		// and carries the D3 fix; the missing-setting panel does not repeat it.
		const block = w.find(".kt-next-step-block");
		expect(block.text()).toContain("Initial submissions are closed");
		expect(block.text()).toContain("You can keep editing this draft, but it cannot be submitted now.");
		expect(block.text()).toContain("Ask your KenTender administrator to complete this setting.");
		expect(block.find("button").exists()).toBe(false);
		expect(w.find('[data-testid="pln-dpp-closed"]').exists()).toBe(false);
		expect(w.text().match(/Initial submissions are closed/g)).toHaveLength(1);
		expect(w.find('[data-testid="pln-missing-setting"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-dpp-context"]').text()).toContain("Status");
		expect(w.find('[data-testid="pln-dpp-save"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-dpp-submit"]').exists()).toBe(false);
	});
});

// PLN-CHG-001 v1.30 §10.4 — certification and the register show the change from the accepted estimate
describe("DppPlanScreen — the accepted requirement's estimate (v1.30)", () => {
	it("shows the accepted estimate and the change beneath a revised amount, and nothing otherwise", () => {
		const changed = { ...LAPTOPS, amount_display: "KES 35,000,000", need_estimate_display: "KES 30,000,000", estimate_change_display: "+KES 5,000,000" };
		const w = make({ plan: plan({ entries: [INFRASTRUCTURE, changed] }) });
		const lines = w.findAll('[data-testid="pln-dpp-estimate-change"]');
		expect(lines).toHaveLength(1);
		expect(lines[0].text()).toBe("Accepted requirement estimate: KES 30,000,000. Change: +KES 5,000,000.");
	});

	it("adds no column and no blocker", () => {
		const changed = { ...LAPTOPS, need_estimate_display: "KES 30,000,000", estimate_change_display: "+KES 5,000,000" };
		const w = make({ plan: plan({ entries: [changed] }) });
		expect(w.findAll("thead th")).toHaveLength(make().findAll("thead th").length);
	});
});
