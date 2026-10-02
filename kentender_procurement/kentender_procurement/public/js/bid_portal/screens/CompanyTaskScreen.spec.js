// BDS-CHG-001 v0.8 §10.9 behaviour of the company task: a declaration opens
// in the response drawer and saves only its own changed answers; Save and
// continue saves the bid's contact and the security answers, then opens the
// next task; a refusal is named in place; Keep bid details changes nothing;
// Use updated details calls the snapshot refresh.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import CompanyTaskScreen from "./CompanyTaskScreen.vue";
import { companyTask } from "./company.fixtures.js";

const REF = "TND-MOH-2027-033";
function portalFor({ call, upload } = {}) {
	const route = ref({ path: `/tenders/${REF}/bid/company`, segments: ["tenders", REF, "bid", "company"], query: {} });
	const go = vi.fn();
	return { call: call || vi.fn(async (m) => (m.endsWith("get_bid_task") ? companyTask() : { ok: true })), upload: upload || vi.fn(async () => ({ ok: true })), go, setTitle: vi.fn(), createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go, epoch: ref(0) }) };
}
function mountWith(initial, portal) {
	return mount(CompanyTaskScreen, { props: { reference: REF, initial }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}
const method = (call, i) => call.mock.calls[i][0].split(".").pop();

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Company, declarations and tender security", () => {
	it("offers the preparer the hand-over wherever the page says the bid waits on the signatory", async () => {
		const task = { ...companyTask(), handover: { signatories: ["Mary Wanjiku"], can_notify: true, last: null, wait_text: "", max_note: 500 } };
		const wrapper = mountWith(task, portalFor());
		await nextTick();
		expect(wrapper.get('[data-testid="bds-handover"] [data-testid="bds-handover-send"]').text()).toBe("Notify Mary Wanjiku");
		const signatory = mountWith(companyTask(), portalFor()); // the read carries none for the signatory
		await nextTick();
		expect(signatory.find('[data-testid="bds-handover"]').exists()).toBe(false);
	});

	it("tells the preparer who can change the signatory and what a missing certificate means", async () => {
		const task = companyTask();
		task.signatory = { ...task.signatory, certificate: { status: "Required", tone: "attention" },
			certificate_note: "Mary Wanjiku needs a digital certificate from the signing service before this bid can be submitted.",
			change_note: "Only an Authorised Signatory of Afya Digital Supplies Limited can change who signs, in the Account under People. Ask Mary Wanjiku.", change_href: "" };
		const wrapper = mountWith(task, portalFor());
		await nextTick();
		expect(wrapper.get('[data-testid="bds-signatory-certificate-note"]').text()).toContain("needs a digital certificate");
		expect(wrapper.get('[data-testid="bds-signatory-change-note"]').text()).toContain("Ask Mary Wanjiku.");
		expect(wrapper.find('[data-testid="bds-signatory-change-note"] a').exists()).toBe(false); // he cannot do it, so no link
		task.signatory = { ...task.signatory, change_note: "You can change who signs in your Account, under People.", change_href: "/account" };
		const signatory = mountWith(task, portalFor());
		await nextTick();
		expect(signatory.get('[data-testid="bds-signatory-change-note"] a').attributes("href")).toBe("/account");
	});

	it("opens a declaration in the drawer and saves only its changed answer", async () => {
		const portal = portalFor();
		const wrapper = mountWith(companyTask("JV"), portal);
		await wrapper.get('[data-testid="bds-declaration-g-decl-1"]').get("button").trigger("click");
		await nextTick();
		const drawer = document.querySelector('[data-testid="bds-response-drawer"]');
		expect(drawer.querySelector('[role="dialog"]').getAttribute("aria-label")).toBe("Form of Tender");
		const box = drawer.querySelector('input[type="checkbox"]');
		box.checked = true;
		box.dispatchEvent(new Event("change"));
		await nextTick();
		drawer.querySelector('[data-testid="bds-drawer-save"]').click();
		await flushPromises();
		expect(method(portal.call, 0)).toBe("save_bid_task");
		expect([portal.call.mock.calls[0][1].task, JSON.parse(portal.call.mock.calls[0][1].values)]).toEqual(["company", { "h-decl-1": true }]);
		expect(method(portal.call, 1)).toBe("get_bid_task"); // the page reloads in place
		expect(document.querySelector('[data-testid="bds-response-drawer"]')).toBeNull();
	});

	it("shows the saved contact and security answers on first paint when the page loads with its data", async () => {
		// a refresh or a direct link mounts the screen with the server's data in hand;
		// the blank form is not what the person typed, so nothing saved is replaced by it
		const task = companyTask("JV");
		const wrapper = mountWith(task, portalFor());
		await flushPromises();
		expect(wrapper.get('[data-testid="bds-contact-email"]').element.value).toBe(task.contact.email);
		expect(wrapper.get('[data-testid="bds-contact-phone"]').element.value).toBe(task.contact.phone);
		const answered = task.tender_security.fields.filter((f) => f.editable && f.kind !== "evidence" && f.value !== null && f.value !== undefined && f.value !== "");
		for (const f of answered) {
			const control = wrapper.find(`[data-testid="bds-company-field-${f.handle}"]`);
			if (control.exists()) expect(control.element.value ?? control.text()).toContain(String(f.value));
		}
	});

	it("makes another person of the organisation the Tender contact (FU-V08-54)", async () => {
		const task = companyTask("JV");
		task.contact = { ...task.contact, people: [{ assignment_id: "ASG-D", name: "David Ouma" }, { assignment_id: "ASG-M", name: "Mary Wanjiku" }], person: "ASG-D" };
		const portal = portalFor({ call: vi.fn(async (m) => (m.endsWith("get_bid_task") ? task : { ok: true })) });
		const wrapper = mountWith(task, portal);
		const person = wrapper.get('[data-testid="bds-contact-person"]');
		expect(person.findAll("option").map((o) => o.text())).toEqual(["David Ouma", "Mary Wanjiku"]);
		await person.setValue("ASG-M");
		await wrapper.get('[data-testid="bds-company-save"]').trigger("click");
		await flushPromises();
		const contact = portal.call.mock.calls.find((c) => c[0].endsWith("update_tender_contact"));
		expect(contact[1]).toMatchObject({ assignment_id: "ASG-M", expected_record_version: 4 });
	});

	it("saves the bid's contact and the security answers, then opens the next task", async () => {
		const portal = portalFor();
		const wrapper = mountWith(companyTask("JV"), portal);
		await wrapper.get('[data-testid="bds-contact-phone"]').setValue("+254 700 000 222");
		await wrapper.get("#bds-security-h-sec-issuer").setValue("Equity Bank");
		await wrapper.get('[data-testid="bds-company-save"]').trigger("click");
		await flushPromises();
		const calls = portal.call.mock.calls.map((c) => c[0].split(".").pop());
		expect(calls).toEqual(["update_tender_contact", "get_bid_task", "save_bid_task"]);
		expect(portal.call.mock.calls[0][1]).toMatchObject({ phone: "+254 700 000 222", expected_record_version: 4 });
		expect(JSON.parse(portal.call.mock.calls[2][1].values)).toEqual({ "h-sec-issuer": "Equity Bank" });
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/requirements`);
	});

	it("changes the Tender notice email to another verified Account email", async () => {
		const portal = portalFor();
		const wrapper = mountWith(companyTask(), portal);
		expect(wrapper.findAll('[data-testid="bds-contact-notice"] option').map((o) => o.text())).toEqual(["tenders@afyadigital.example", "bids@afyadigital.example"]);
		await wrapper.get('[data-testid="bds-contact-notice"]').setValue("C2");
		await wrapper.get('[data-testid="bds-company-save"]').trigger("click");
		await flushPromises();
		expect(method(portal.call, 0)).toBe("update_tender_notice_contact");
		expect(portal.call.mock.calls[0][1]).toMatchObject({ bidder_arrangement_id: "ARR-MOH-2027-033-001", notice_contact_id: "C2", expected_record_version: 4 });
		expect(portal.go).toHaveBeenCalledWith(`/tenders/${REF}/bid/requirements`);
	});

	it("names a refused contact phone in place and stays", async () => {
		const call = vi.fn(async () => ({ ok: false, errors: { phone: "Enter the Tender contact's telephone number, for example +254 709 555 015." } }));
		const portal = portalFor({ call });
		const wrapper = mountWith(companyTask(), portal);
		await wrapper.get('[data-testid="bds-contact-phone"]').setValue("abc");
		await wrapper.get('[data-testid="bds-company-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.text()).toContain("Enter the Tender contact's telephone number");
		expect(wrapper.get('[data-testid="bds-contact-phone"]').element.value).toBe("abc");
		expect(portal.go).not.toHaveBeenCalled();
	});

	it("Keep bid details closes the comparison without a command; Use updated details refreshes the snapshot", async () => {
		const portal = portalFor();
		const wrapper = mountWith(companyTask("ACCOUNT-UPDATE"), portal);
		await wrapper.get('[data-testid="bds-keep-bid"]').trigger("click");
		expect(wrapper.find('[data-testid="bds-account-update"]').exists()).toBe(false);
		expect(portal.call).not.toHaveBeenCalled();
		const again = mountWith(companyTask("ACCOUNT-UPDATE"), portal);
		await again.get('[data-testid="bds-use-updated"]').trigger("click");
		await flushPromises();
		expect(method(portal.call, 0)).toBe("refresh_bid_organisation_snapshot");
		expect(portal.call.mock.calls[0][1]).toMatchObject({ confirm: 1, expected_record_version: 20 });
	});

	it("keeps unsaved security entries when a file command re-reads the page", async () => {
		const portal = portalFor({ call: vi.fn(async (m) => (m.endsWith("get_bid_task") ? companyTask("JV") : { ok: true })) });
		const wrapper = mountWith(companyTask("JV"), portal);
		await wrapper.get("#bds-security-h-sec-issuer").setValue("Equity Bank");
		const input = wrapper.get("#bds-security-h-sec-proof");
		Object.defineProperty(input.element, "files", { value: [new File(["%PDF-1.4"], "g.pdf", { type: "application/pdf" })] });
		await input.trigger("change");
		await flushPromises();
		expect(portal.call.mock.calls.map((c) => c[0].split(".").pop())).toContain("get_bid_task");
		expect(wrapper.get("#bds-security-h-sec-issuer").element.value).toBe("Equity Bank");
	});

	it("shows the physical original as the bid knows it, and uploads proof as its own command", async () => {
		const portal = portalFor();
		const wrapper = mountWith(companyTask("SECURITY"), portal);
		expect(wrapper.get('[data-testid="bds-security-physical"]').text()).toContain("Physical original not yet recorded");
		const input = wrapper.get("#bds-security-h-sec-proof");
		const file = new File(["%PDF-1.4"], "guarantee.pdf", { type: "application/pdf" });
		Object.defineProperty(input.element, "files", { value: [file] });
		await input.trigger("change");
		await flushPromises();
		const [m, fields, files] = portal.upload.mock.calls[0];
		expect([m.split(".").pop(), fields.handle, fields.expected_record_version, files.file]).toEqual(["upload_bid_evidence", "h-sec-proof", 20, file]);
	});
});
