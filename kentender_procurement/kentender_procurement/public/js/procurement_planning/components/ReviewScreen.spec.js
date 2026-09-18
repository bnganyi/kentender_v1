// PLN-CHG-001 v1.23 §10.10 — ReviewScreen component tests (U11).
//
// Every governance actor reads the same document; only the header, the prior
// accountability, the statement and the buttons change. And the decision comes
// before the collapsed evidence, with every material issue already visible.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReviewScreen from "./ReviewScreen.vue";

const ITEMS = [
	{
		plan_item_id: "PPI-MOH-2027-021",
		title: "National digital health infrastructure upgrade",
		purpose: "Priority health facilities can use secure and interoperable digital health services.",
		quantity_number: "1",
		unit_label: "Programme",
		delivery_completion_display: "31 Aug 2027",
		value_display: "KES 80,000,000",
		procurement_method: "Open Tender",
		department: "Digital Health",
	},
	{
		plan_item_id: "PPI-MOH-2027-033",
		title: "Clinical training and deployment laptops for digital health rollout",
		purpose: "Clinical training teams can use the common digital-health platform during training.",
		quantity_number: "250",
		unit_label: "Each",
		delivery_completion_display: "31 Dec 2027",
		value_display: "KES 50,000,000",
		procurement_method: "Open Tender",
		department: "Digital Health / Human Resources Management and Development",
	},
];

function task(overrides = {}) {
	return {
		outcome: "OK",
		task: "AOT-MOH-2027-001-V1",
		status: "Open",
		stage: "Accounting Officer adoption",
		can_decide: true,
		can_decide_positive: true,
		can_download_review_pack: true,
		plan_reference: "PLN-MOH-2027-001",
		version_number: 1,
		header: { title: "Ministry of Health Annual Procurement Plan 2027/28" },
		authority_card: { capacity_detail: "Responsible Cabinet Secretary", is_board: false },
		decision_summary: {
			value_display: "KES 130,000,000",
			purchases: 2,
			departments: 2,
			funding: "Within approved budget",
			funding_kind: "live",
			reservation: "Required allocation met",
			reservation_kind: "live",
			schedule: "All purchases meet departmental deadlines",
			issues: [],
		},
		items: ITEMS,
		caption: "2 Plan Items · KES 130,000,000",
		funding: {
			rows: [],
			at_approval: { actor_name: "Josphat Mwangi", decided_at_display: "4 Dec 2026, 10:00 EAT" },
		},
		reservation: { required_allocation_display: "KES 48,000,000", planned_qualifying_display: "KES 50,000,000", budget_basis_reference: "MOH-BUD-2027-001", budget_version_display: "Version 1" },
		preparation_signature: {
			actor_name: "Charles Mutiso",
			capacity: "Head of Procurement Function",
			signed_at_display: "7 Dec 2026, 10:00 EAT",
		},
		history: [],
		changes: { is_initial: true },
		late_activation_required: false,
		...overrides,
	};
}

function make(props = {}) {
	return mount(ReviewScreen, {
		props: { task: task(), resolution: "", lateReason: "", pending: false, errorSummary: "", ...props },
	});
}

describe("ReviewScreen — U11-AO shared composition", () => {
	it("opens with the decision summary, not with evidence", () => {
		const w = make();
		const summary = w.find('[data-testid="rev-summary"]');
		expect(summary.text()).toContain("KES 130,000,000");
		expect(summary.text()).toContain("Estimated cost");
		expect(summary.text()).toContain("Purchases");
		expect(summary.text()).toContain("Departments");
		const checks = w.find('[data-testid="rev-checks"]');
		expect(checks.text()).toContain("Within approved budget");
		expect(checks.text()).toContain("Required allocation met");
		expect(checks.text()).toContain("All purchases meet departmental deadlines");
	});

	it("says there are no blocking issues only when there are none", () => {
		const w = make();
		expect(w.find('[data-testid="rev-no-issues"]').text()).toBe("No blocking issues");
		expect(w.find('[data-testid="rev-issue"]').exists()).toBe(false);
	});

	it("lists purchases with their source-grounded purpose, none expanded", () => {
		const w = make();
		const rows = w.findAll('[data-testid="rev-purchase-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Priority health facilities can use secure and interoperable digital health services.");
		// PLN22-AC-008 — no purchase starts expanded.
		expect(w.find('[data-testid="rev-purchase-detail"]').exists()).toBe(false);
	});

	it("opens one purchase's detail deliberately", async () => {
		const w = make();
		await w.findAll('[data-testid="rev-review-purchase"]')[0].trigger("click");
		expect(w.find('[data-testid="rev-purchase-detail"]').text()).toContain("Open Tender");
	});

	it("keeps every evidence section closed", () => {
		const w = make();
		for (const id of ["rev-funding-evidence", "rev-plan-checks", "rev-history"]) {
			expect(w.find(`[data-testid="${id}"]`).attributes("open")).toBeUndefined();
		}
	});

	it("shows funding and preparation accountability as two compact rows", () => {
		const w = make();
		const accountability = w.find('[data-testid="rev-accountability"]');
		expect(accountability.text()).toContain("Checked by Josphat Mwangi");
		expect(w.find('[data-testid="rev-preparation"]').text()).toContain("Charles Mutiso, Head of Procurement Function");
	});

	it("does not require the review pack to decide", () => {
		const w = make();
		expect(w.find('[data-testid="rev-download"]').exists()).toBe(true);
		expect(w.find('[data-testid="rev-confirm"]').attributes("disabled")).toBeUndefined();
	});
});

describe("ReviewScreen — only the actor's own part changes", () => {
	it("U11-HOPF: signs, has no Return, and shows no preparation row yet", () => {
		const w = make({ task: task({ stage: "Head of Procurement Function", preparation_signature: null }) });
		expect(w.find('[data-testid="rev-title"]').text()).toBe("Review and submit the annual procurement plan");
		expect(w.find('[data-testid="rev-confirm"]').text()).toBe("Sign and submit Annual Plan");
		expect(w.find('[data-testid="rev-secondary"]').text()).toBe("Back to annual plan");
		expect(w.find('[data-testid="rev-preparation"]').exists()).toBe(false);
	});

	it("U11-AO: adopts and sends on", () => {
		const w = make();
		expect(w.find('[data-testid="rev-title"]').text()).toBe("Review the annual procurement plan");
		expect(w.find('[data-testid="rev-confirm"]').text()).toBe("Adopt and submit");
		expect(w.find('[data-testid="rev-statement"]').text()).toContain("you adopt the complete plan shown here");
	});

	it("U11-STATUTORY: approves, and says activation is still to come", () => {
		const w = make({ task: task({ stage: "Statutory approval" }) });
		expect(w.find('[data-testid="rev-title"]').text()).toBe("Approve the annual procurement plan");
		expect(w.find('[data-testid="rev-confirm"]').text()).toBe("Approve Annual Procurement Plan");
		expect(w.find('[data-testid="rev-statement"]').text()).toContain(
			"Publication and activation checks must still be completed.",
		);
	});

	it("U11-COLLECTIVE: records the body's decision and requires the resolution", () => {
		const w = make({
			task: task({
				stage: "Statutory approval",
				authority_card: { capacity_detail: "Council", is_board: true },
				recorder_name: "Naomi Chebet",
			}),
		});
		expect(w.find('[data-testid="rev-title"]').text()).toBe("Record the Council's decision");
		const collective = w.find('[data-testid="rev-collective"]');
		expect(collective.text()).toContain("Decision belongs to");
		expect(collective.text()).toContain("Council");
		expect(collective.text()).toContain("Naomi Chebet");
		expect(w.find('[data-testid="rev-resolution"]').exists()).toBe(true);
		expect(w.find('[data-testid="rev-confirm"]').text()).toBe("Record approval");
		// Not a personal approval, and no member-by-member voting.
		expect(w.find('[data-testid="rev-statement"]').text()).toBe("Record approval only if the body approved this plan.");
	});

	it("U11-READER: shows the same document and no decision area", () => {
		const w = make({ task: task({ can_decide: false, status: "Completed", historical: true }) });
		expect(w.find('[data-testid="rev-footer"]').exists()).toBe(false);
		expect(w.find('[data-testid="rev-statement"]').exists()).toBe(false);
		expect(w.find('[data-testid="rev-historical"]').text()).toBe("Historical plan — read only");
		// The complete content is still there.
		expect(w.findAll('[data-testid="rev-purchase-row"]')).toHaveLength(2);
		expect(w.find('[data-testid="rev-summary"]').exists()).toBe(true);
	});
});

describe("ReviewScreen — a decision never precedes a hidden issue", () => {
	it("U11-STALE-EVIDENCE: shows the issue and removes the positive decision", () => {
		const w = make({
			task: task({
				can_decide_positive: false,
				decision_summary: {
					...task().decision_summary,
					funding: "Funding needs to be checked again",
					funding_kind: "critical",
					issues: [
						"The budget has changed since Finance checked this plan. Procurement must obtain a new funding check before this plan can be adopted.",
					],
				},
			}),
		});
		expect(w.find('[data-testid="rev-no-issues"]').exists()).toBe(false);
		expect(w.find('[data-testid="rev-issue"]').text()).toContain("The budget has changed since Finance checked this plan.");
		expect(w.find('[data-testid="rev-confirm"]').exists()).toBe(false);
		// The corrective action stays available.
		expect(w.find('[data-testid="rev-secondary"]').text()).toBe("Return for correction");
	});

	it("U11-LATE-ADOPTION: asks why before the decision, with no editable date", () => {
		const w = make({
			task: task({ late_activation_required: true, financial_year_started_display: "1 Jul 2027" }),
		});
		const late = w.find('[data-testid="rev-late"]');
		expect(late.text()).toContain("Financial year started");
		expect(late.text()).toContain("1 Jul 2027");
		expect(w.find('[data-testid="rev-late-reason"]').exists()).toBe(true);
		// No backdating control.
		expect(w.findAll('input[type="date"]')).toHaveLength(0);
	});
});
