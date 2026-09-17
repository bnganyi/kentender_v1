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
		update_notice: null,
		...overrides,
	};
}

function make(props = {}) {
	return mount(DppPlanScreen, {
		props: { plan: plan(), pending: false, certified: false, errorSummary: "", ...props },
	});
}

describe("DppPlanScreen — U02-AUTHOR-DRAFT", () => {
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
				...extra,
			}),
		});
	}

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
				accepted_submission_number: 1,
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
		expect(w.find('[data-testid="pln-dpp-correction-notice"]').text()).toContain("Your plan needs a correction");
		expect(w.find('[data-testid="pln-dpp-issue"]').text()).toContain(
			"Explain how the KES 30,000,000 estimate for the deployment laptops was calculated",
		);
		expect(w.find('[data-testid="pln-dpp-submit"]').text()).toBe("Resubmit departmental plan");
		// New requirements belong in the next update, and there is no add
		// action here to suggest otherwise.
		expect(w.find('[data-testid="pln-dpp-next-update"]').text()).toContain(
			"Finish this correction first. New requirements belong in the next update.",
		);
	});

	it("keeps a closed-intake draft editable while saying it cannot be submitted", () => {
		const w = make({
			plan: plan({ context: { ...plan().context, window: { state: "Closed", display: "Closed" } } }),
		});
		expect(w.find('[data-testid="pln-dpp-closed"]').text()).toBe(
			"Initial submissions are closed. You can keep editing this draft, but it cannot be submitted now.",
		);
		expect(w.find('[data-testid="pln-dpp-save"]').exists()).toBe(true);
		expect(w.find('[data-testid="pln-dpp-submit"]').exists()).toBe(false);
	});
});
