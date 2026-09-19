// TPR-DES-10/11/12 — addendum variants, inquiry effect choice, cancellation
// grounds/consequences/obligations, and the confirmation dialog's own checks.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AddendumScreen from "./AddendumScreen.vue";
import InquiryScreen from "./InquiryScreen.vue";
import CancelScreen from "./CancelScreen.vue";
import ChannelConfirmationDialog from "./ChannelConfirmationDialog.vue";
import EvidenceDialog from "./EvidenceDialog.vue";

const TENDER = { name: "TDR-1", tender_reference: "TND-MOH-2027-033", overall_status: "Published — open", record_version: 9, current_deadline_label: "5 Jun 2027, 11:00 EAT", badge: "Published — open" };
const REFS = [{ key: "delivery_location", label: "Goods and delivery — delivery location", area: "Goods/delivery schedule", value: "Central Warehouse, Nairobi", material: false }, { key: "authorised_value", label: "Authorised value", area: "Evaluation or contract term", value: "KES 50,000,000.00", material: true }];
const RULE = { required: true, current_deadline_label: "5 Jun 2027, 11:00 EAT", explanation: "This addendum is being issued within the governed late-amendment period." };
const ADD = { name: "TDA-1", status: "Draft", change_class: "Administrative clarification", affected_area: "Goods/delivery schedule", affected_reference_key: "delivery_location", revised_value: "Loading Bay 3", reason: "Loading bay reassigned.", materiality_statement: "Same site.", revised_submission_deadline: "2027-06-12 11:00:00", record_version: 1 };
const DATA = { tender: TENDER, addendum: ADD, references: REFS, change_classes: ["Administrative clarification", "Submission deadline extension"], affected_areas: ["Goods/delivery schedule"], deadline_rule: RULE, channels: [], original_channels: [{ channel: "STATE_PORTAL", label: "State Portal" }], editable: true, allowed_actions: ["save_addendum_draft", "submit_addendum_for_issue"], material: false };

describe("AddendumScreen — TPR-DES-10", () => {
	it("draft: editable fields, the current published value, the deadline rule and Save/Submit", async () => {
		const w = mount(AddendumScreen, { props: { data: DATA, identity: "TDA-1:1:9", errors: {}, pending: false } });
		expect(w.find('[data-testid="tnd-record-badge"]').text()).toBe("Draft addendum");
		expect(w.find('[data-testid="tnd-ad-previous"]').text()).toBe("Central Warehouse, Nairobi");
		expect(w.find('[data-testid="tnd-deadline-rule"]').text()).toContain("Submission deadline must be extended.");
		expect(w.find('[data-testid="tnd-addendum-channels"] tbody').text()).toContain("State Portal");
		await w.find('[data-testid="tnd-ad-submit"]').trigger("click");
		expect(w.emitted("submit")[0][0]).toMatchObject({ affected_reference_key: "delivery_location", revised_value: "Loading Bay 3", revised_submission_deadline: "2027-06-12 11:00:00" });
	});
	it("material change: the critical notice, no form and Submit disabled", async () => {
		const w = mount(AddendumScreen, { props: { data: DATA, identity: "TDA-1:1:9", errors: {}, pending: false } });
		await w.find('[data-testid="tnd-ad-reference"]').setValue("authorised_value");
		expect(w.find('[data-testid="tnd-addendum-material"]').text()).toContain("This change cannot be made by addendum.");
		expect(w.find('[data-testid="tnd-deadline-rule"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-ad-reference"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-ad-submit"]').attributes("disabled")).toBeDefined();
	});
	it("HOPF issue: read-only facts, Ready to issue, Return / Issue", () => {
		const w = mount(AddendumScreen, { props: { data: { ...DATA, addendum: { ...ADD, status: "Awaiting issue" }, editable: false, allowed_actions: ["return_addendum_for_correction", "issue_addendum"] }, identity: "x", errors: {}, pending: false } });
		expect(w.find('[data-testid="tnd-addendum-ready"]').text()).toContain("Ready to issue.");
		expect(w.find("textarea").exists()).toBe(false);
		expect(w.findAll(".tnd-footer button").map((b) => b.text())).toEqual(["Return for correction", "Issue addendum"]);
	});
});

describe("InquiryScreen — TPR-DES-11", () => {
	const data = { tender: TENDER, inquiry: { name: "TDI-1", addendum_reference: "ADD-MOH-2027-033-001", candidate_label: "Verified supplier account", candidate_identity: "", question: "Does the clarified delivery point apply to all lots?", received_at_label: "1 Jun 2027, 09:00 EAT", status: "Awaiting response" }, effect_texts: { no: "The response will be sent to the candidate and recorded.", yes: "The response will be sent to every registered candidate without identifying who asked." }, allowed_actions: ["send_response"] };
	it("never shows the candidate identity to the responder and switches the effect text", async () => {
		const w = mount(InquiryScreen, { props: { data, pending: false, error: "" } });
		expect(w.find('[data-testid="tnd-inq-candidate"]').text()).toBe("Verified supplier account");
		expect(w.find('[data-testid="tnd-inq-effect"]').text()).toBe("The response will be sent to the candidate and recorded.");
		await w.find('[data-testid="tnd-inq-affects-yes"]').trigger("change");
		expect(w.find('[data-testid="tnd-inq-effect"]').text()).toContain("without identifying who asked");
		await w.find('[data-testid="tnd-inq-response"]').setValue("Yes, it applies to all lots.");
		await w.find('[data-testid="tnd-inq-send"]').trigger("click");
		expect(w.emitted("send")[0][0]).toEqual({ response: "Yes, it applies to all lots.", affects_requirements: true });
	});
	it("late: the deadline notice and no Send control", () => {
		const w = mount(InquiryScreen, { props: { data: { ...data, inquiry: { ...data.inquiry, status: "Late" }, allowed_actions: [], late_text: "The inquiry deadline has passed." }, pending: false, error: "" } });
		expect(w.find('[data-testid="tnd-inq-late"]').text()).toContain("The inquiry deadline has passed.");
		expect(w.find('[data-testid="tnd-inq-send"]').exists()).toBe(false);
	});
});

describe("CancelScreen — TPR-DES-12", () => {
	const data = { tender: TENDER, summary: { purchase: "Laptops", tender: "TND-MOH-2027-033", published_at: "15 May 2027, 08:00 EAT", submission_deadline: "5 Jun 2027, 11:00 EAT", channel_count: 4 }, grounds: [{ key: "INADEQUATE_BUDGET", label: "Inadequate budgetary provision" }], recommendation: { by_name: "Charles Mutiso", text: "Delivery timeline no longer meets user-department need." }, consequences: { ppra_report_due_by: "18 Jun 2027", candidate_notice_due_by: "18 Jun 2027", replacement_text: "A replacement procurement requires new governance." }, cancellation: null, allowed_actions: ["cancel_tender"] };
	it("AO decision: warning, summary, recommendation, ground/reason, consequences; reason bound inline", async () => {
		const w = mount(CancelScreen, { props: { data, pending: false, error: "" } });
		expect(w.find('[data-testid="tnd-cancel-warning"]').text()).toContain("Cancellation is final for this Tender.");
		expect(w.find('[data-testid="tnd-recommendation"]').text()).toContain("Recommended by Charles Mutiso, HOPF.");
		expect(w.find('[data-testid="tnd-consequences"]').text()).toContain("PPRA report due 18 Jun 2027.");
		await w.find('[data-testid="tnd-cancel-open-dialog"]').trigger("click");
		expect(w.find('[data-testid="tnd-cancel-error"]').text()).toContain("20–2,000 characters");
		expect(w.emitted("cancel")).toBeUndefined();
		await w.find('[data-testid="tnd-cancel-reason"]').setValue("The confirmed budget available for this procurement is insufficient to proceed.");
		await w.find('[data-testid="tnd-cancel-open-dialog"]').trigger("click");
		expect(w.emitted("cancel")[0][0]).toMatchObject({ ground: "INADEQUATE_BUDGET", ground_label: "Inadequate budgetary provision" });
	});
	it("cancelled detail: decided-by facts and obligations with Record evidence only for outstanding rows", () => {
		const cancelled = { ...data, tender: { ...TENDER, overall_status: "Cancelled" }, cancellation: { decided_by_name: "Amina Hassan", decided_at_label: "10 Jun 2027, 09:30 EAT", ground_label: "Inadequate budgetary provision", reason: "Insufficient.", obligations: [{ obligation_id: "OB-1", obligation_type: "PPRA report", label: "PPRA report", due_by: "18 Jun 2027", status: "Due" }, { obligation_id: "OB-2", obligation_type: "Candidate notice", label: "Candidate notices", due_by: "18 Jun 2027", status: "Recorded", evidence_reference: "CN-1", recorded_by_name: "Brian" }] }, allowed_actions: ["record_cancellation_evidence"] };
		const w = mount(CancelScreen, { props: { data: cancelled, pending: false, error: "" } });
		expect(w.find('[data-testid="tnd-cancelled-facts"]').text()).toContain("Amina Hassan, Accounting Officer");
		expect(w.findAll('[data-testid="tnd-record-evidence"]')).toHaveLength(1);
		expect(w.find('[data-testid="tnd-obligation-OB-1"] .kt-status').text()).toBe("Outstanding");
		expect(w.find('[data-testid="tnd-obligation-OB-2"] .kt-status').text()).toBe("Recorded");
		expect(w.find('[data-testid="tnd-cancel-open-dialog"]').exists()).toBe(false);
	});
});

describe("ChannelConfirmationDialog + EvidenceDialog", () => {
	it("refuses to confirm without the attestation and file, inline, and asks for a URL on an online channel", async () => {
		const w = mount(ChannelConfirmationDialog, { props: { channel: { channel: "STATE_PORTAL", channel_label: "State Portal" }, attestation: "I confirm.", pending: false, error: "" } });
		expect(w.find(".kt-dialog-title").text()).toBe("Confirm State Portal publication");
		expect(w.find('[data-testid="tnd-ch-url"]').exists()).toBe(true);
		await w.find('[data-testid="tnd-ch-confirm"]').trigger("click");
		expect(w.emitted("confirm")).toBeUndefined();
		expect(w.find('[data-testid="tnd-ch-error-evidence_file"]').text()).toBe("Attach the publication evidence file.");
		expect(w.find('[data-testid="tnd-ch-error-attestation"]').exists()).toBe(true);
	});
	it("EvidenceDialog offers only published requirements to prove and refuses a blank choice", async () => {
		const w = mount(EvidenceDialog, { props: { row: null, inherited: { technical_requirements: [{ technical_requirement_id: "TR-001", label: "Electrical compatibility", required_value: "Yes", unit: "" }] }, pending: false, error: "" } });
		expect(w.findAll('[data-testid="tnd-ev-proves"] option').map((o) => o.text())).toEqual(["Choose the published requirement", "Electrical compatibility — Yes"]);
		await w.find('[data-testid="tnd-ev-label"]').setValue("Electrical compatibility certificate");
		await w.find('[data-testid="tnd-ev-confirm"]').trigger("click");
		expect(w.find('[data-testid="tnd-ev-error-proves"]').exists()).toBe(true);
		await w.find('[data-testid="tnd-ev-proves"]').setValue("TR-001");
		await w.find('[data-testid="tnd-ev-confirm"]').trigger("click");
		expect(w.emitted("confirm")[0][0]).toEqual({ label: "Electrical compatibility certificate", evidence_type: "Certificate", linked_requirement_type: "Technical requirement", linked_requirement_id: "TR-001", mandatory: true });
	});
});
