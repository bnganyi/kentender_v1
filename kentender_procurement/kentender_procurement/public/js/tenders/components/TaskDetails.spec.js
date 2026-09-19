// TPR-DES-03 — hydration on identity only, the meeting variants, the
// payload's date/time forms and the server field errors shown inline.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import TaskDetails from "./TaskDetails.vue";

const VALUES = { tender_title: "Supply and delivery of business laptops", issue_date: "2027-05-15", clarification_deadline: "2027-05-27 17:00:00", submission_deadline: "2027-06-05 11:00:00", tender_validity_days: 120, tender_security_amount: 500000, pre_tender_meeting: false };

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

	it("renders the server's field errors next to their inputs", () => {
		const w = mount(TaskDetails, { props: { values: VALUES, options: {}, identity: "TDR-1:3", errors: { tender_security_amount: "Enter a positive amount." } } });
		expect(w.find('[data-testid="tnd-error-tender_security_amount"]').text()).toBe("Enter a positive amount.");
	});
});
