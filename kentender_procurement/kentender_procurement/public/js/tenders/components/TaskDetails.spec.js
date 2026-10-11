// TPR-DES-03 — hydration on identity only, the meeting variants, the
// payload's date/time forms and the server field errors shown inline.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import TaskDetails from "./TaskDetails.vue";

const VALUES = { tender_title: "Supply and delivery of business laptops", issue_date: "2027-05-15", clarification_deadline: "2027-05-27 17:00:00", submission_deadline: "2027-06-05 11:00:00", tender_validity_days: 120, tender_security_amount: 500000, tender_security_method: "Bidder uploads an electronic instrument", tender_security_original: "Required", pre_tender_meeting: false };

describe("TaskDetails — TPR-DES-03", () => {
	it("hydrates once per identity and builds the payload in the server's own forms", async () => {
		const w = mount(TaskDetails, { props: { values: VALUES, options: { delivery_locations: ["Afya House"] }, identity: "TDR-1:1", errors: {} } });
		expect(w.find('[data-testid="tnd-field-tender_title"]').element.value).toBe("Supply and delivery of business laptops");
		expect(w.find('[data-testid="tnd-field-tender_security_amount"]').element.value).toBe("500,000.00");
		await w.find('[data-testid="tnd-field-tender_title"]').setValue("Edited title");
		// a server echo with the same identity never clobbers the officer's edit
		await w.setProps({ values: { ...VALUES, tender_title: "Server" } });
		expect(w.find('[data-testid="tnd-field-tender_title"]').element.value).toBe("Edited title");
		const payload = w.vm.getPayload();
		expect(payload.tender_title).toBe("Edited title");
		expect(payload.clarification_deadline).toBe("2027-05-27 17:00:00");
		expect(payload.tender_security_amount).toBe("500000.00");
		expect(payload.pre_tender_meeting).toBe(false);
		expect(payload.meeting_mode).toBeUndefined();
		expect(w.vm.isDirty()).toBe(true);
	});

	it("states how tender security may be submitted and whether an original is delivered, chosen explicitly (no default)", async () => {
		const blank = mount(TaskDetails, { props: { values: { ...VALUES, tender_security_method: undefined, tender_security_original: undefined }, options: {}, identity: "TDR-1:9", errors: {} } });
		expect(blank.find('[data-testid="tnd-field-tender_security_method"]').element.value).toBe("");
		expect(blank.find('[data-testid="tnd-field-tender_security_original"]').element.value).toBe("");
		expect(blank.vm.getPayload().tender_security_method).toBeUndefined(); // an unchosen value is never sent, so the server says it is missing
		const w = mount(TaskDetails, { props: { values: VALUES, options: {}, identity: "TDR-1:8", errors: { tender_security_method: "Choose one of: Electronic." } } });
		await w.find('[data-testid="tnd-field-tender_security_method"]').setValue("Paper instrument requiring an original");
		// a paper instrument always needs its original: the choice follows the method
		expect(w.find('[data-testid="tnd-field-tender_security_original"]').element.value).toBe("Required");
		expect(w.vm.getPayload()).toMatchObject({ tender_security_method: "Paper instrument requiring an original", tender_security_original: "Required" });
		await w.find('[data-testid="tnd-field-tender_security_method"]').setValue("Issuer supplies the instrument directly");
		await w.find('[data-testid="tnd-field-tender_security_original"]').setValue("Not required");
		expect(w.vm.getPayload()).toMatchObject({ tender_security_method: "Issuer supplies the instrument directly", tender_security_original: "Not required" });
		expect(w.find('[data-testid="tnd-security-method-help"]').text()).toContain("bidders enter its details and upload nothing");
		expect(w.find('[data-testid="tnd-error-tender_security_method"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-security-method-help"]').text()).toContain("does not by itself require a physical original");
	});

	it("shows the venue for a physical meeting and the joining information for an online one", async () => {
		const w = mount(TaskDetails, { props: { values: { ...VALUES, pre_tender_meeting: true, meeting_mode: "Physical", meeting_datetime: "2027-05-22 10:00:00", meeting_venue: "Afya House" }, options: { delivery_locations: ["Afya House"] }, identity: "TDR-1:2", errors: {} } });
		expect(w.find('[data-testid="tnd-field-meeting_venue"]').exists()).toBe(true);
		expect(w.find('[data-testid="tnd-field-online_joining_information"]').exists()).toBe(false);
		await w.find('[data-testid="tnd-mode-online"]').trigger("change");
		expect(w.find('[data-testid="tnd-field-online_joining_information"]').exists()).toBe(true);
		expect(w.vm.getPayload().meeting_mode).toBe("Online");
		await w.find('[data-testid="tnd-meeting-no"]').trigger("change");
		expect(w.find('[data-testid="tnd-field-meeting_datetime"]').exists()).toBe(false);
	});

	// v0.16 §5.2 — the two preparation-period numbers come from the server (`period_rule`); the form hints, pre-fills and asks for a reason,
	// the server decides at review.
	const RULE = { minimum_days: 7, default_days: 21, closing_time: "11:00" };
	const mountWith = (values) => mount(TaskDetails, { props: { values, options: {}, identity: "TDR-1:1", errors: {}, periodRule: RULE } });

	it("states the legal minimum and the usual period under the submission deadline", () => {
		const w = mountWith(VALUES);
		expect(w.find('[data-testid="tnd-period-hint"]').text()).toBe("At least 7 days after the issue date (the legal minimum). The usual tendering period is 21 days.");
		expect(mount(TaskDetails, { props: { values: VALUES, options: {}, identity: "x", errors: {} } }).find('[data-testid="tnd-period-hint"]').exists()).toBe(false);
	});

	it("pre-fills the submission deadline from the issue date only while the officer has not entered one", async () => {
		const w = mountWith({ ...VALUES, issue_date: "", submission_deadline: "", clarification_deadline: "" });
		await w.find('[data-testid="tnd-field-issue_date"]').setValue("2027-05-15");
		expect(w.find('[data-testid="tnd-field-submission_deadline"]').element.value).toBe("2027-06-05T11:00");
		// a later change of the issue date moves the suggestion, until the officer edits the deadline
		await w.find('[data-testid="tnd-field-issue_date"]').setValue("2027-05-20");
		expect(w.find('[data-testid="tnd-field-submission_deadline"]').element.value).toBe("2027-06-10T11:00");
		await w.find('[data-testid="tnd-field-submission_deadline"]').setValue("2027-06-01T09:00");
		await w.find('[data-testid="tnd-field-issue_date"]').setValue("2027-05-25");
		expect(w.find('[data-testid="tnd-field-submission_deadline"]').element.value).toBe("2027-06-01T09:00");
		// a deadline that was already there is never replaced
		const kept = mountWith(VALUES);
		await kept.find('[data-testid="tnd-field-issue_date"]').setValue("2027-05-01");
		expect(kept.find('[data-testid="tnd-field-submission_deadline"]').element.value).toBe("2027-06-05T11:00");
	});

	it("asks for a reason only when the period is shorter than the usual one, and sends it", async () => {
		const w = mountWith({ ...VALUES, issue_date: "2099-05-15", submission_deadline: "2099-06-05 11:00:00" });
		expect(w.find('[data-testid="tnd-field-shortened_period_reason"]').exists()).toBe(false);
		await w.find('[data-testid="tnd-field-submission_deadline"]').setValue("2099-05-30T11:00");
		const reason = w.find('[data-testid="tnd-field-shortened_period_reason"]');
		expect(reason.exists()).toBe(true);
		expect(w.find('[data-testid="tnd-period-reason-help"]').text()).toContain("shorter than the usual 21 days");
		await reason.setValue("Needed before the October training.");
		expect(w.vm.getPayload().shortened_period_reason).toBe("Needed before the October training.");
		await w.find('[data-testid="tnd-field-submission_deadline"]').setValue("2099-06-15T11:00");
		expect(w.find('[data-testid="tnd-field-shortened_period_reason"]').exists()).toBe(false);
		expect(w.vm.getPayload().shortened_period_reason).toBeUndefined();
	});

	it("renders the server's field errors next to their inputs", () => {
		const w = mount(TaskDetails, { props: { values: VALUES, options: {}, identity: "TDR-1:3", errors: { tender_security_amount: "Enter a positive amount." } } });
		expect(w.find('[data-testid="tnd-error-tender_security_amount"]').text()).toBe("Enter a positive amount.");
	});
});
