// TPR-DES-05 — server-decided actions: Return/Approve only for an open task
// read by the Head of Procurement Function; SoD note when blocked.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ApprovalTaskScreen from "./ApprovalTaskScreen.vue";

function task(permitted) {
	return {
		task: "TPK-1", task_status: "Open",
		tender: { tender_reference: "TND-MOH-2099-001", version_number: 1, requirement_title: "Business laptops" },
		inherited: { requisition_reference: "REQ-MOH-2099-001", counts: { items: 1, related_services: 0, acceptance_requirements: 1 }, goods: [{ description: "Business laptops", quantity: 1, minimum_warranty: "24 months" }], authorised_value: "KES 1", planned_method: "Open Tender", internal_context: { strategic_objective_path: "SO-1 › KR-1", plan_horizon: "Single-year" } },
		officer_values: { tender_security_amount: 500000, submission_deadline: "2100-06-05 11:00:00", tender_validity_days: 120, payment_timing_days: "30", performance_security_required: true, performance_security_percent: 10, delay_damages_per_week_percent: 0.5, maximum_delay_damages_percent: 10, contract_contact_office: "Office" },
		readiness: { blocking_count: 0, warning_count: 1, findings: [{ severity: "Warning", finding_code: "WARN_MANUFACTURER_AUTHORISATION" }] },
		renders: { invitation_digest: "a".repeat(64), issued_tender_digest: "b".repeat(64) },
		evidence_requirements: [{}, {}],
		binding: { template_version: "1.1", bundle_digest: "c".repeat(64), requisition_content_digest: "d".repeat(64) },
		permitted_actions: permitted,
	};
}

describe("ApprovalTaskScreen — TPR-DES-05", () => {
	it("renders the immutable summary with the internal-only context and the readiness warning suffix", () => {
		const w = mount(ApprovalTaskScreen, { props: { task: task({ can_return: true, can_approve: true }) } });
		expect(w.find(".tpr-cap").text()).toBe("TND-MOH-2099-001 · Version 1");
		expect(w.find(".kt-status").text()).toBe("Submitted for approval");
		expect(w.find('[data-testid="tpr-approval-internal-context"]').text()).toContain("Internal only — never rendered to bidders");
		expect(w.find('[data-testid="tpr-approval-readiness"]').text()).toContain("1 Warning — manufacturer authorisation proportionality");
		expect(w.findAll("input, select, textarea").length).toBe(0);
	});

	it("shows Return and Approve only when the server permits, and the SoD note when blocked", async () => {
		const open = mount(ApprovalTaskScreen, { props: { task: task({ can_return: true, can_approve: true }) } });
		await open.find('[data-testid="tpr-approve"]').trigger("click");
		expect(open.emitted("approve")).toBeTruthy();
		await open.find('[data-testid="tpr-return"]').trigger("click");
		expect(open.emitted("return")).toBeTruthy();
		const sod = mount(ApprovalTaskScreen, { props: { task: task({ can_return: true, can_approve: false, sod_blocked: true }) } });
		expect(sod.find('[data-testid="tpr-approve"]').attributes("disabled")).toBeDefined();
		expect(sod.find('[data-testid="tpr-sod-note"]').text()).toContain("another Head of Procurement Function must approve it");
		const reader = mount(ApprovalTaskScreen, { props: { task: task({ can_return: false, can_approve: false }) } });
		expect(reader.find('[data-testid="tpr-approve"]').exists()).toBe(false);
		expect(reader.find('[data-testid="tpr-return"]').exists()).toBe(false);
	});

	it("emits preview with the named output", async () => {
		const w = mount(ApprovalTaskScreen, { props: { task: task({}) } });
		await w.find('[data-testid="tpr-approval-preview-invitation"]').trigger("click");
		expect(w.emitted("preview")[0]).toEqual(["invitation"]);
	});
});
