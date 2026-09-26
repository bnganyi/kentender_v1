// TPR-DES-10/11/12 — addendum variants, the clarification answer, cancellation
// grounds/consequences/obligations, and the confirmation dialog's own checks.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { addendumData, clarificationData } from "./fixtures.js";
import AddendumScreen from "./AddendumScreen.vue";
import ClarificationScreen from "./ClarificationScreen.vue";
import CancelScreen from "./CancelScreen.vue";
import ChannelConfirmationDialog from "./ChannelConfirmationDialog.vue";
import EvidenceDialog from "./EvidenceDialog.vue";

const TENDER = { name: "TDR-1", tender_reference: "TND-MOH-2027-033", overall_status: "Published — open", record_version: 9, current_deadline_label: "5 Jun 2027, 11:00 EAT", badge: "Published — open" };
const REFS = [{ key: "delivery_location", label: "Goods and delivery — delivery location", area: "Goods/delivery schedule", value: "Central Warehouse, Nairobi", material: false }, { key: "authorised_value", label: "Authorised value", area: "Evaluation or contract term", value: "KES 50,000,000.00", material: true }];
const RULE = { required: true, current_deadline_label: "5 Jun 2027, 11:00 EAT", explanation: "This addendum is being issued within the governed late-amendment period." };
const ADD = { name: "TDA-1", status: "Draft", change_class: "Administrative clarification", affected_area: "Goods/delivery schedule", affected_reference_key: "delivery_location", revised_value: "Loading Bay 3", reason: "Loading bay reassigned.", materiality_statement: "Same site.", revised_submission_deadline: "2027-06-12 11:00:00", record_version: 1 };
const DATA = { tender: TENDER, addendum: ADD, references: REFS, change_classes: ["Administrative clarification", "Submission deadline extension"], affected_areas: ["Goods/delivery schedule"], deadline_rule: RULE, channels: [], original_channels: [{ channel: "STATE_PORTAL", label: "State Portal" }], editable: true, allowed_actions: ["save_addendum_draft", "submit_addendum_for_issue"], material: false };

describe("AddendumScreen — TPR-DES-10", () => {
	it("draft: the scope warning, the editable form, the current value, the deadline consequence, Save/Submit", async () => {
		const w = mount(AddendumScreen, { props: { data: addendumData("DRAFT"), identity: "a:1", pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-addendum-scope"]').text()).toContain("A material change requires cancellation");
		expect(w.find('[data-testid="tnd-ad-previous"]').text()).toBe("Ministry of Health Headquarters, Afya House, Nairobi");
		expect(w.find('[data-testid="tnd-deadline-rule"] h2').text()).toBe("Submission deadline must be extended");
		expect(w.findAll('[data-testid="tnd-addendum-channels"] tbody tr')).toHaveLength(4);
		await w.find('[data-testid="tnd-ad-submit"]').trigger("click");
		expect(w.emitted("submit")[0][0].affected_reference_key).toBe("delivery_location");
		expect(w.find('[data-kt="next-step"]').text()).toContain("Submit the non-material addendum for issue.");
		w.unmount();
	});
	it("material change: the comparison only, the blocked guidance with its fixes, no Submit", async () => {
		const w = mount(AddendumScreen, { props: { data: addendumData("MATERIAL"), identity: "a:2", pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-addendum-form"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-addendum-comparison"] tbody').text()).toContain("300 Each");
		expect(w.findAll('[data-kt="next-step"] button').map((b) => b.text())).toEqual(["Ask Amina Hassan (Accounting Officer) to consider cancellation", "Discard addendum draft"]);
		expect(w.find('[data-testid="tnd-ad-submit"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-view-cancellation-requirements"]').exists()).toBe(true);
		w.unmount();
	});
	it("HOPF issue: the comparison, the deadline read-only, Return / Issue", async () => {
		const w = mount(AddendumScreen, { props: { data: addendumData("HOPF"), identity: "a:3", pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-addendum-comparison"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-ad-deadline"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-ad-return"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-ad-issue"]').text()).toBe("Issue addendum");
		w.unmount();
	});
	it("closed review: the recorded reason and only Discard", async () => {
		const w = mount(AddendumScreen, { props: { data: addendumData("MATERIAL-CLOSED"), identity: "a:4", pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-review-closed-reason"]').text()).toContain("separate procurement");
		expect(w.findAll('[data-kt="next-step"] button').map((b) => b.text())).toEqual(["Discard addendum draft"]);
		w.unmount();
	});
});

describe("ClarificationScreen — TPR-DES-11", () => {
	it("an ordinary answer: the registration caveat, the audience choice, Send response", async () => {
		const w = mount(ClarificationScreen, { props: { data: clarificationData(), pending: false, error: "" }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-clarification-candidate"]').text()).toBe("Registered Tender candidate");
		expect(w.text()).toContain("It does not confirm supplier qualification or eligibility.");
		expect(w.find('[data-kt="next-step"]').text()).toContain("Send the answer to all registered candidates.");
		await w.find('[data-testid="tnd-clar-response"]').setValue("Yes, they may be from different customers.");
		await w.find('[data-testid="tnd-clar-send"]').trigger("click");
		expect(w.emitted("send")[0][0]).toEqual({ response: "Yes, they may be from different customers.", affects_published_tender: false, response_audience: "All registered candidates", required_addendum: "" });
		w.unmount();
	});
	it("an unsaved Yes shows the server's published-change answer: no audience, no Send, Prepare addendum", async () => {
		const w = mount(ClarificationScreen, { props: { data: clarificationData("CHANGE"), pending: false, error: "" }, attachTo: document.body });
		await nextTick();
		await w.find('[data-testid="tnd-clar-changes-yes"]').trigger("change");
		await nextTick();
		const step = w.find('[data-kt="next-step"]');
		expect(step.classes()).toContain("is-warning");
		expect(step.text()).toContain("A clarification cannot change requirements, criteria, dates or supplier obligations on its own.");
		expect(step.find("button").text()).toBe("Prepare addendum");
		expect(w.find('[data-testid="tnd-clar-audience"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-clar-send"]').exists()).toBe(false);
		w.unmount();
	});
	it("a delivery failure: the recorded answer, the protected recipient and Retry notice", async () => {
		const w = mount(ClarificationScreen, { props: { data: clarificationData("FAILURE"), pending: false, error: "" }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-clar-recorded-response"]').text()).toContain("does not require both contracts");
		expect(w.find('[data-testid="tnd-clar-notices"] tbody').text()).toContain("procurement@failed-delivery.example");
		expect(w.find('[data-kt="next-step"] button').text()).toBe("Retry notice");
		expect(w.find('[data-testid="tnd-clar-send"]').exists()).toBe(false);
		w.unmount();
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
