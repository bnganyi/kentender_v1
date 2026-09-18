// PLN-CHG-001 v1.23 §10.15 — CorrectionRequestsScreen component tests (U16).
//
// The required change leads; identifiers follow. One hold covers every
// unresolved request and states what is left. The permanent scope restriction
// is a separate fact that outlives the hold, and nothing anywhere offers to
// restart stopped downstream work.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import CorrectionRequestsScreen from "./CorrectionRequestsScreen.vue";

function request(overrides = {}) {
	return {
		request: "UI-COR-01",
		change_required: "Confirm the funding allocation",
		status: "Needs review",
		status_kind: "pending",
		requested_from: "Digital Health",
		action: "Review issue",
		terminal: false,
		record_version: 1,
		can_start: true,
		can_record_completed: false,
		can_close_without_change: true,
		completion_blocked_reason: "Prepare and activate a plan correction before recording it here.",
		detail: {
			request: "UI-COR-01",
			requisition_reference: "REQ-MOH-2027-015",
			requisition_version: "2",
			requested_by: "mercy@kentender.test",
			requested_display: "9 Dec 2026, 09:00 EAT",
			plan_version: "APV-MOH-2027-001-V1",
			resolved_by: "",
			resolved_display: "",
			resolution_note: "",
		},
		...overrides,
	};
}

function task(overrides = {}) {
	return {
		outcome: "OK",
		plan_item_id: "PPI-MOH-2027-033",
		title: "Clinical training and deployment laptops for digital health rollout",
		version_number: 1,
		hold: {
			active: true,
			text: "New requisitions for this purchase are on hold until the planning issue is resolved.",
			remaining: "2 issues still need attention",
		},
		scope_lock: { locked: false },
		requests: [
			request(),
			request({
				request: "UI-COR-02",
				change_required: "Correct the description without increasing the planned scope",
				status: "Correction in progress",
				status_kind: "attention",
				action: "Continue correction",
				can_start: false,
				detail: { ...request().detail, request: "UI-COR-02" },
			}),
		],
		correcting_plan: { available: false },
		additional_requirement: null,
		can_act: true,
		...overrides,
	};
}

function make(props = {}) {
	return mount(CorrectionRequestsScreen, {
		props: { task: task(), openIssue: "", pending: false, errorSummary: "", ...props },
	});
}

describe("CorrectionRequestsScreen — U16 BASE", () => {
	it("leads with what must change, not with the request id", () => {
		const w = make();
		const rows = w.findAll('[data-testid="cor-issue-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Confirm the funding allocation");
		expect(rows[1].text()).toContain("Correct the description without increasing the planned scope");
		// The identifiers exist, but not in the table.
		expect(w.find('[data-testid="cor-issues"]').text()).not.toContain("UI-COR-01");
	});

	it("names the status and whose issue it is, with the lawful next action", () => {
		const w = make();
		const rows = w.findAll('[data-testid="cor-issue-row"]');
		expect(rows[0].text()).toContain("Needs review");
		expect(rows[0].text()).toContain("Digital Health");
		expect(rows[0].find('[data-testid="cor-issue-action"]').text()).toBe("Review issue");
		expect(rows[1].find('[data-testid="cor-issue-action"]').text()).toBe("Continue correction");
	});

	it("shows the hold once, over both issues", () => {
		const w = make();
		expect(w.findAll('[data-testid="cor-hold"]')).toHaveLength(1);
		expect(w.find('[data-testid="cor-hold"]').text()).toContain(
			"New requisitions for this purchase are on hold until the planning issue is resolved.",
		);
	});
});

describe("CorrectionRequestsScreen — U16-OPEN-DETAIL", () => {
	it("keeps the mechanics in the detail, opened deliberately", async () => {
		const w = make();
		expect(w.find('[data-testid="cor-issue-detail"]').exists()).toBe(false);

		await w.findAll('[data-testid="cor-issue-action"]')[0].trigger("click");
		expect(w.emitted("open-issue")[0][0]).toBe("UI-COR-01");

		const open = make({ openIssue: "UI-COR-01" });
		const detail = open.find('[data-testid="cor-issue-detail"]');
		expect(detail.text()).toContain("UI-COR-01");
		expect(detail.text()).toContain("REQ-MOH-2027-015");
		expect(detail.text()).toContain("9 Dec 2026, 09:00 EAT");
		expect(detail.find('[data-testid="cor-prepare-correction"]').text()).toBe("Prepare plan correction");
		// No manual scope unlock, ever.
		expect(open.text()).not.toContain("Unlock");
	});

	it("says why completion is not offered instead of showing a dead control", () => {
		const w = make({ openIssue: "UI-COR-01" });
		expect(w.find('[data-testid="cor-record-completed"]').exists()).toBe(false);
		expect(w.find('[data-testid="cor-completion-blocked"]').text()).toContain(
			"Prepare and activate a plan correction before recording it here.",
		);
	});
});

describe("CorrectionRequestsScreen — U16-COMPLETE", () => {
	it("names the exact correcting plan before offering to record it", () => {
		const w = make({
			openIssue: "UI-COR-01",
			task: task({
				requests: [request({ can_record_completed: true, can_start: false, completion_blocked_reason: "" })],
				correcting_plan: {
					available: true,
					plan_reference: "PLN-MOH-2027-001",
					correcting_plan_version: "APV-MOH-2027-001-V2",
					version_number: 2,
					activated_display: "16 Dec 2026, 09:00 EAT",
					update_in_preparation: false,
				},
			}),
		});
		const plan = w.find('[data-testid="cor-correcting-plan"]');
		expect(plan.text()).toContain("PLN-MOH-2027-001");
		expect(plan.text()).toContain("2");
		expect(plan.text()).toContain("16 Dec 2026, 09:00 EAT");
		expect(w.find('[data-testid="cor-record-completed"]').text()).toBe("Record correction completed");
	});

	it("says a plan update in preparation is not yet a correction", () => {
		const w = make({
			openIssue: "UI-COR-01",
			task: task({
				requests: [request({ completion_blocked_reason: "A plan update is being prepared. Record the correction once that version is active." })],
				correcting_plan: { available: true, plan_reference: "PLN-MOH-2027-001", correcting_plan_version: "APV-MOH-2027-001-V1", version_number: 1, activated_display: "", update_in_preparation: true },
			}),
		});
		expect(w.find('[data-testid="cor-record-completed"]').exists()).toBe(false);
		expect(w.find('[data-testid="cor-completion-blocked"]').text()).toContain("once that version is active");
	});
});

describe("CorrectionRequestsScreen — U16-MULTIPLE", () => {
	it("keeps the hold and counts what is still outstanding", () => {
		const w = make({
			task: task({
				hold: {
					active: true,
					text: "New requisitions for this purchase are on hold until the planning issue is resolved.",
					remaining: "1 issue still needs attention",
				},
				requests: [
					request({ status: "Correction recorded", status_kind: "live", terminal: true, action: "View outcome", can_start: false, can_close_without_change: false }),
					request({ request: "UI-COR-02", detail: { ...request().detail, request: "UI-COR-02" } }),
				],
			}),
		});
		expect(w.find('[data-testid="cor-hold-remaining"]').text()).toBe("1 issue still needs attention");
		// Resolving one never offers to restart the stopped downstream work.
		expect(w.text()).not.toContain("Resume requisitions");
	});
});

describe("CorrectionRequestsScreen — U16-PERMANENT-SCOPE", () => {
	it("keeps the restriction after every request is resolved, with no restored badge", () => {
		const w = make({
			task: task({
				hold: { active: false },
				scope_lock: {
					locked: true,
					text: "A requisition has already been authorised. Extra requirements must be added as a separate purchase in a plan update.",
					first_requisition: "REQ-MOH-2027-010",
				},
				requests: [request({ status: "Correction recorded", status_kind: "live", terminal: true, action: "View outcome", can_start: false, can_close_without_change: false, detail: { ...request().detail, resolved_display: "16 Dec 2026, 10:00 EAT", resolved_by: "mercy@kentender.test", resolution_note: "Resolved against APV-MOH-2027-001-V2." } })],
			}),
			openIssue: "UI-COR-01",
		});
		expect(w.find('[data-testid="cor-hold"]').exists()).toBe(false);
		expect(w.find('[data-testid="cor-scope-lock"]').text()).toContain("separate purchase in a plan update");
		expect(w.find('[data-testid="cor-outcome"]').text()).toContain("16 Dec 2026, 10:00 EAT");
		expect(w.text()).not.toContain("restored");
	});
});

describe("CorrectionRequestsScreen — U16-ADDITIONAL-REQUIREMENT", () => {
	it("states three separate results and offers only the separate-item route", async () => {
		const w = make({
			task: task({
				additional_requirement: {
					heading: "Requirement not yet in the current plan",
					sources: [
						{
							dpp_entry: "DPE-0099",
							entry_id: "DPP-MOH-DH-2027-004",
							title: "Additional deployment laptops",
							department: "Digital Health",
							quantity_display: "50 Each",
							amount_display: "KES 10,000,000",
							source_label: "Accepted Need · NEED-MOH-DH-2027-014",
							annual_plan_result: "Not yet in the current annual plan",
							procurement_result: "No procurement recorded",
							completion_result: "No completion evidence",
						},
					],
					action: "Add as a separate item in a plan update",
					route: ["annual-procurement-plan", "PLN-MOH-2027-001"],
				},
			}),
		});
		const block = w.find('[data-testid="cor-additional"]');
		expect(block.text()).toContain("Digital Health");
		expect(block.text()).toContain("50 Each");
		expect(block.text()).toContain("KES 10,000,000");
		expect(block.text()).toContain("DPP-MOH-DH-2027-004");

		const results = w.find('[data-testid="cor-additional-results"]');
		expect(results.text()).toContain("Not yet in the current annual plan");
		expect(results.text()).toContain("No procurement recorded");
		expect(results.text()).toContain("No completion evidence");

		// The action navigates; it never creates an update on its own.
		await w.find('[data-testid="cor-add-separate"]').trigger("click");
		expect(w.emitted("navigate")[0][0]).toEqual(["annual-procurement-plan", "PLN-MOH-2027-001"]);
	});
});

describe("CorrectionRequestsScreen — a reader who cannot act", () => {
	it("keeps every fact and offers no control", () => {
		const w = make({ openIssue: "UI-COR-01", task: task({ can_act: false }) });
		expect(w.find('[data-testid="cor-issue-detail"]').text()).toContain("REQ-MOH-2027-015");
		expect(w.find('[data-testid="cor-issue-footer"]').exists()).toBe(false);
		expect(w.find('[data-testid="cor-prepare-correction"]').exists()).toBe(false);
	});
});
