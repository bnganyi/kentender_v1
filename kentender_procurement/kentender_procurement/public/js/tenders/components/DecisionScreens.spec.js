// TPR-DES-05/06/07/08/09 — the decision screens render the server's result,
// segregation and allowed actions; absent actions are absent, never disabled.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import { approvalData, authorisationData, publicationData, reviewData, reviewRecord } from "./fixtures.js";
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
	// §10.17 DES-05: the guidance region replaces the result notice and the
	// must-fix notices; the review note stays separate; Submit is present only
	// while the server permits it.
	it("Ready to submit: Your turn to submit, the review note with its link, facts, sections, Submit", async () => {
		const review = reviewData();
		const w = mount(ReviewScreen, { props: { record: reviewRecord(), review, pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-kt="next-step"]').text()).toContain("Submit this Tender for approval.");
		expect(w.find('[data-kt="journey"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-review-result-ready"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-review-notes"]').text()).toContain("1 review note.");
		await w.find('[data-testid="tnd-review-note-link"]').trigger("click");
		expect(w.emitted("go-finding")[0][0].task).toBe("requirements");
		expect(w.find('[data-testid="tnd-submit-for-approval"]').attributes("disabled")).toBeUndefined();
		expect(w.find('[data-testid="tnd-section-tag-supplier"]').text()).toBe("1 review note");
		expect(w.findAll('[data-testid="tnd-key-facts"] .kt-label').map((l) => l.text())).toEqual(["Requisition", "Quantity", "Approved value", "Method", "Submission deadline", "Tender security", "Reservation", "Latest delivery"]);
		w.unmount();
	});
	it("Needs attention: Your turn, blocked names the item and its fix; no Submit, no duplicate notice", async () => {
		const w = mount(ReviewScreen, { props: { record: reviewRecord(), review: reviewData("BLOCKED"), pending: false }, attachTo: document.body });
		await nextTick();
		const block = w.find('[data-kt="next-step"]');
		expect(block.classes()).toContain("is-warning");
		expect(block.text()).toContain("Enter the inspection and acceptance location.");
		await block.find("button").trigger("click");
		expect(w.emitted("fix")[0][0].label).toBe("Review contract terms");
		expect(w.find('[data-testid="tnd-must-fix"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-submit-for-approval"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-section-contract"] .kt-disclosure-body').exists()).toBe(true);
		w.unmount();
	});
});

describe("ApprovalScreen — TPR-DES-06", () => {
	it("normal: Your turn to decide, the submitted row, both decisions", async () => {
		const w = mount(ApprovalScreen, { props: { ...approvalData(), pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-kt="next-step"]').text()).toContain("Decide whether to approve this Tender package.");
		expect(w.find('[data-testid="tnd-ready-to-approve"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-submitted-row"]').text()).toContain("Brian Wafula");
		expect(w.find('[data-testid="tnd-return-for-correction"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-approve-package"]').text()).toBe("Approve Tender package");
		// the HOPF reviews, never edits: the note's link opens its section in place
		await w.find('[data-testid="tnd-review-note-link"]').trigger("click");
		expect(w.find('[data-testid="tnd-section-supplier"] .kt-disclosure-body').exists()).toBe(true);
		w.unmount();
	});
	it("segregation: the waiting line carries the reason; no decision control at all", async () => {
		const w = mount(ApprovalScreen, { props: { ...approvalData("SEGREGATION"), pending: false }, attachTo: document.body });
		await nextTick();
		const step = w.find('[data-kt="next-step"]');
		expect(step.attributes("data-kind")).toBe("waiting");
		expect(step.text()).toContain("You cannot approve a Tender Version you prepared or submitted.");
		expect(w.find('[data-testid="tnd-segregation"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-approve-package"]').exists()).toBe(false);
		expect(w.find('[data-testid="tnd-return-for-correction"]').exists()).toBe(false);
		w.unmount();
	});
});

describe("AuthorisationScreen — TPR-DES-07", () => {
	it("shows the read-only channel table with no selector and the one decision", async () => {
		const w = mount(AuthorisationScreen, { props: { pub: authorisationData(), pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-testid="tnd-channel-table"] tbody').text()).toContain("State Portal");
		expect(w.find('[data-testid="tnd-channel-table"] select, [data-testid="tnd-channel-table"] input').exists()).toBe(false);
		expect(w.find(".kt-bar").exists()).toBe(false);
		expect(w.find('[data-testid="tnd-package-digest"]').text()).toContain("aaaa");
		expect(w.find('[data-testid="tnd-authorise-publication"]').text()).toBe("Authorise publication");
		expect(w.text()).not.toContain("Mark as published");
		w.unmount();
	});
	it("segregation hides the decision and explains it in the waiting line", async () => {
		const w = mount(AuthorisationScreen, { props: { pub: authorisationData("SEGREGATION"), pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-kt="next-step"]').text()).toContain("A System Manager must assign an eligible Accounting Officer");
		expect(w.find('[data-testid="tnd-authorise-publication"]').exists()).toBe(false);
		w.unmount();
	});
});

describe("PublicationScreen — TPR-DES-08", () => {
	it("the guidance states the count once; Confirm publication on outstanding rows for the HoPF only", async () => {
		const w = mount(PublicationScreen, { props: { pub: publicationData(), pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-kt="next-step"]').text()).toContain("2 of 4 channels are confirmed.");
		expect(w.find('[data-testid="tnd-publication-progress"]').exists()).toBe(false);
		expect(w.find(".kt-bar").exists()).toBe(false);
		expect(w.findAll('[data-testid="tnd-confirm-channel"]')).toHaveLength(2);
		w.unmount();
		const reader = mount(PublicationScreen, { props: { pub: { ...publicationData(), allowed_actions: [] }, pending: false } });
		expect(reader.findAll('[data-testid="tnd-confirm-channel"]')).toHaveLength(0);
	});
	it("a refusal replaces the guidance with its blocked answer; a conflict draws its inline row", async () => {
		const invalid = publicationData("INVALID");
		const w = mount(PublicationScreen, { props: { pub: invalid, refusal: invalid._refusal, pending: false }, attachTo: document.body });
		await nextTick();
		expect(w.find('[data-kt="next-step"]').classes()).toContain("is-warning");
		expect(w.findAll('[data-kt="next-step"] button').map((b) => b.text())).toEqual(["Choose evidence file", "Confirm publication"]);
		w.unmount();
		const conflict = publicationData("CONFLICT");
		const c = mount(PublicationScreen, { props: { pub: conflict, refusal: conflict._refusal, conflict: conflict._conflict, pending: false } });
		expect(c.find('[data-testid="tnd-already-confirmed"]').text()).toContain("The later confirmation request changed nothing.");
	});
});

describe("PublishedScreen — TPR-DES-09", () => {
	const base = { tender: { ...TENDER, badge: "Published — open", overall_status: "Published — open", published_at_label: "15 May 2027, 08:00 EAT", submission_deadline_label: "12 Jun 2027, 11:00 EAT" }, publication: { authorised_by_name: "Amina Hassan", channels: [], published_at_label: "15 May 2027, 08:00 EAT" }, open_period: { addenda: [], clarifications: [], effective_addenda_count: 0, empty_addenda_text: "No addenda have been issued." }, documents: [], decisions: [], allowed_actions: [] };
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
