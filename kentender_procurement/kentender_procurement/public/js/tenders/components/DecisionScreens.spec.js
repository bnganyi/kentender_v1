// TPR-DES-05/06/07/08/09 — the decision screens render the server's result,
// segregation and allowed actions; absent actions are absent, never disabled.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import ReviewScreen from "./ReviewScreen.vue";
import ApprovalScreen from "./ApprovalScreen.vue";
import AuthorisationScreen from "./AuthorisationScreen.vue";
import PublicationScreen from "./PublicationScreen.vue";
import PublishedScreen from "./PublishedScreen.vue";

const TENDER = { name: "TDR-1", tender_reference: "TND-MOH-2027-033", requisition_reference: "REQ-MOH-2027-033-001", title: "Supply and delivery of business laptops", badge: "Draft", overall_status: "Draft", record_version: 3 };
const FACTS = [{ label: "Purchase", value: "Supply and delivery of business laptops" }, { label: "Submission deadline", value: "5 Jun 2027, 11:00 EAT" }];
const SECTIONS = [{ key: "details", title: "Tender details", summary: "Issue 15 May 2027", open: false, details: { fields: [{ label: "Purchase", value: "x" }] } }, { key: "supplier", title: "Supplier and evaluation requirements", summary: "Manufacturer authorisation", open: true, details: { qualification: [{ criterion: "Manufacturer's authorisation", required: true }], evidence_requirements: [] } }];
const NOTE = { finding_code: "PROPORTIONALITY", severity: "Review note", message: "Confirm that manufacturer authorisation is proportionate for this purchase.", task: "requirements", field: "manufacturer_authorisation_required", link_label: "Review supplier requirements" };
const MUST = { finding_code: "REQUIRED", severity: "Must fix", message: "Enter the inspection and acceptance location.", task: "requirements", field: "inspection_location", link_label: "Review contract terms" };

describe("ReviewScreen — TPR-DES-05", () => {
	it("Ready to submit: result notice, review note with its link, facts, sections, enabled Submit", async () => {
		const w = mount(ReviewScreen, { props: { record: { tender: TENDER, tasks: { details: "Complete", requirements: "Complete", review: "Complete" }, allowed_actions: ["submit_for_approval"] }, review: { review: { result: "Ready to submit", must_fix: [], review_notes: [NOTE], must_fix_count: 0, findings: [NOTE] }, key_facts: FACTS, sections: SECTIONS, allowed_actions: ["submit_for_approval"] }, pending: false } });
		expect(w.find('[data-testid="tnd-review-result-ready"]').text()).toContain("Ready to submit.");
		expect(w.find('[data-testid="tnd-review-notes"]').text()).toContain("1 review note.");
		await w.find('[data-testid="tnd-review-notes"] button').trigger("click");
		expect(w.emitted("go-finding")[0][0].task).toBe("requirements");
		expect(w.find('[data-testid="tnd-submit-for-approval"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="tnd-section-supplier"] .tnd-tag').text()).toBe("1 review note");
	});
	it("Needs attention: the Must fix notice, the disabled Submit and its reason", () => {
		const w = mount(ReviewScreen, { props: { record: { tender: TENDER, tasks: { details: "Complete", requirements: "Needs attention", review: "Not started" }, allowed_actions: [] }, review: { review: { result: "Needs attention", must_fix: [MUST], review_notes: [], must_fix_count: 1, findings: [MUST] }, key_facts: FACTS, sections: SECTIONS, submit_blocked_text: "Fix the item above before submitting." }, pending: false } });
		expect(w.find('[data-testid="tnd-review-result-blocked"]').text()).toContain("Needs attention.");
		expect(w.find('[data-testid="tnd-must-fix"]').text()).toContain("Enter the inspection and acceptance location.");
		expect(w.find('[data-testid="tnd-submit-for-approval"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="tnd-submit-blocked-text"]').text()).toBe("Fix the item above before submitting.");
	});
});

describe("ApprovalScreen — TPR-DES-06", () => {
	const record = { tender: { ...TENDER, badge: "Awaiting your approval" }, version: { submitted_by_name: "Brian Wafula", submitted_at_label: "15 Apr 2027, 09:15 EAT", version_number: 2 }, allowed_actions: ["return_for_correction", "approve_tender_package"], segregation_message: "" };
	it("normal: Ready to approve, the submitted row, both decisions", () => {
		const w = mount(ApprovalScreen, { props: { record, review: { review: { must_fix: [], review_notes: [NOTE] }, key_facts: FACTS, sections: SECTIONS }, pending: false } });
		expect(w.find('[data-testid="tnd-ready-to-approve"]').text()).toContain("It does not publish the Tender.");
		expect(w.find('[data-testid="tnd-submitted-row"]').text()).toContain("Brian Wafula");
		expect(w.find('[data-testid="tnd-return-for-correction"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-approve-package"]').text()).toBe("Approve Tender package");
	});
	it("segregation: the critical notice and no decision control at all", () => {
		const w = mount(ApprovalScreen, { props: { record: { ...record, allowed_actions: [], segregation_message: "You cannot approve a Tender Version you prepared or submitted. Another Head of Procurement Function must decide it." }, review: { review: {}, key_facts: [], sections: [] }, pending: false } });
		expect(w.find('[data-testid="tnd-segregation"]').text()).toContain("Another Head of Procurement Function must decide it.");
		expect(w.find('[data-testid="tnd-approve-package"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-return-for-correction"]').exists()).toBe(false);
	});
});

describe("AuthorisationScreen — TPR-DES-07", () => {
	const pub = { tender: { ...TENDER, badge: "Awaiting publication authorisation" }, approval_trail: { prepared_by_name: "Brian Wafula", approved_by_name: "Charles Mutiso", approved_at_label: "20 Apr 2027, 10:00 EAT", version_number: 2 }, review: { review_notes: [NOTE], must_fix: [] }, key_facts: [...FACTS, { label: "Tendering period", value: "77 days" }], proposed_channels: [{ channel: "STATE_PORTAL", label: "State Portal", how: "HOPF confirmation with evidence", result: "Not started" }], rule: { minimum_preparation_days: 21 }, sections: SECTIONS, allowed_actions: ["authorise_publication"], segregation_message: "" };
	it("shows the read-only channel table with no selector and the one decision", () => {
		const w = mount(AuthorisationScreen, { props: { pub, pending: false } });
		expect(w.find('[data-testid="tnd-channel-table"] tbody').text()).toContain("State Portal");
		expect(w.find('[data-testid="tnd-channel-table"] select, [data-testid="tnd-channel-table"] input').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-authorise-publication"]').text()).toBe("Authorise publication");
		expect(w.text()).not.toContain("Mark as published");
	});
	it("segregation hides the decision", () => {
		const w = mount(AuthorisationScreen, { props: { pub: { ...pub, allowed_actions: [], segregation_message: "You cannot authorise publication of a Tender Version you prepared, submitted or approved as Head of Procurement Function. Another Accounting Officer must decide it." }, pending: false } });
		expect(w.find('[data-testid="tnd-segregation"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-authorise-publication"]').exists()).toBe(false);
	});
});

describe("PublicationScreen — TPR-DES-08", () => {
	const rows = [
		{ channel: "STATE_PORTAL", channel_label: "State Portal", status: "Confirmed", result_label: "Confirmed", available_at_label: "15 May 2027, 08:00 EAT" },
		{ channel: "NOTICE_BOARD", channel_label: "Notice board", status: "Awaiting confirmation", result_label: "Awaiting confirmation", available_at_label: "" },
	];
	const pub = { tender: { ...TENDER, badge: "Publication confirmation required" }, publication: { channels: rows, authorised_by_name: "Amina Hassan", authorised_at_label: "15 May 2027, 07:55 EAT", rule_snapshot_id: "PUB-RULE", minimum_preparation_days: 21 }, allowed_actions: ["confirm_publication_channel"] };
	it("counts confirmations, offers Confirm publication to the HoPF only, and the two notices", () => {
		const w = mount(PublicationScreen, { props: { pub, invalidEvidence: true, conflict: rows[0], pending: false } });
		expect(w.find('[data-testid="tnd-publication-progress"]').text()).toContain("1 of 2 required channels confirmed.");
		expect(w.findAll('[data-testid="tnd-confirm-channel"]')).toHaveLength(1);
		expect(w.find('[data-testid="tnd-invalid-evidence"]').text()).toContain("cannot be used as publication evidence");
		expect(w.find('[data-testid="tnd-already-confirmed"]').text()).toContain("already confirmed");
		const reader = mount(PublicationScreen, { props: { pub: { ...pub, allowed_actions: [] }, pending: false } });
		expect(reader.find('[data-testid="tnd-confirm-channel"]').exists()).toBe(false);
	});
});

describe("PublishedScreen — TPR-DES-09", () => {
	const base = { tender: { ...TENDER, badge: "Published — open", overall_status: "Published — open", published_at_label: "15 May 2027, 08:00 EAT", submission_deadline_label: "12 Jun 2027, 11:00 EAT" }, publication: { authorised_by_name: "Amina Hassan", channels: [], published_at_label: "15 May 2027, 08:00 EAT" }, open_period: { addenda: [], inquiries: [], effective_addenda_count: 0, empty_addenda_text: "No addenda have been issued.", empty_inquiries_text: "No addendum inquiries have been received." }, documents: [], decisions: [], allowed_actions: [] };
	it("HoPF: Recommend cancellation + Prepare addendum; AO: Cancel Tender; reader: no action", () => {
		const hopf = mount(PublishedScreen, { props: { record: { ...base, allowed_actions: ["prepare_addendum", "recommend_cancellation", "view_history"] }, review: {}, pending: false } });
		expect(hopf.findAll(".tnd-footer button").map((b) => b.text())).toEqual(["Recommend cancellation", "Prepare addendum"]);
		expect(hopf.find('[data-testid="tnd-no-addenda"]').text()).toBe("No addenda have been issued.");
		const ao = mount(PublishedScreen, { props: { record: { ...base, allowed_actions: ["cancel_tender", "view_history"] }, review: {}, pending: false } });
		expect(ao.findAll(".tnd-footer button").map((b) => b.text())).toEqual(["Cancel Tender"]);
		const reader = mount(PublishedScreen, { props: { record: { ...base, allowed_actions: ["view_history"] }, review: {}, pending: false } });
		expect(reader.find('[data-testid="tnd-no-action"]').text()).toBe("No business action available for this role.");
	});
	it("submission ended: the pending badge, the ended deadline and no open-period action", () => {
		const w = mount(PublishedScreen, { props: { record: { ...base, tender: { ...base.tender, badge: "Submission period ended", overall_status: "Submission period ended" }, allowed_actions: ["prepare_addendum"] }, review: {}, pending: false } });
		expect(w.find('[data-testid="tnd-record-badge"]').classes()).toContain("is-pending");
		expect(w.find('[data-testid="tnd-published-facts"]').text()).toContain("(ended)");
		expect(w.find('[data-testid="tnd-prepare-addendum"]').exists()).toBe(false);
	});
});
