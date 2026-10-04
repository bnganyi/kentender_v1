// BDS-CHG-001 v0.8 §10.4–10.5 behaviour of the Account portal screens: what
// each read shows, what each action sends, and that refusals are named in
// place with the entry kept (never a Message dialog).
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { nextTick, ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import AccountScreen from "./AccountScreen.vue";
import RegisterScreen from "./RegisterScreen.vue";
import { NEW_ACCOUNT, REGISTERED, account, businessProfile } from "./account.fixtures.js";

function portalFor({ call, upload, query = {} } = {}) {
	const route = ref({ path: "/account", segments: ["account"], query });
	return {
		call: call || vi.fn(async () => account()), upload: upload || vi.fn(async () => REGISTERED), go: vi.fn(), setTitle: vi.fn(),
		createSequenceGuard, createCommandRunner, createScreenCache, useRoute: () => ({ route, go: vi.fn(), epoch: ref(0) }),
	};
}
function mountWith(component, props, portal) {
	return mount(component, { props, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
}

afterEach(() => {
	globalThis.__narrow = false;
	document.body.innerHTML = "";
});

describe("Set up your supplier account", () => {
	it("names every refused field in place and keeps what was entered", async () => {
		const upload = vi.fn(async () => ({ ok: false, code: "BDS_FIELD_INVALID", errors: { official_phone: "Enter a phone number using digits, spaces and an optional leading +.", authority_evidence: "Upload the evidence of your authority to sign for the organisation." } }));
		const wrapper = mountWith(RegisterScreen, { initial: NEW_ACCOUNT }, portalFor({ upload }));
		await wrapper.get('[data-testid="acc-legal-name"]').setValue("Afya Digital Supplies Limited");
		await wrapper.get('[data-testid="acc-create"]').trigger("click");
		await flushPromises();
		expect(wrapper.text()).toContain("Enter a phone number using digits");
		expect(wrapper.text()).toContain("Upload the evidence of your authority");
		expect(wrapper.get('[data-testid="acc-phone"]').attributes("aria-invalid")).toBe("true");
		expect(wrapper.get('[data-testid="acc-legal-name"]').element.value).toBe("Afya Digital Supplies Limited");
		expect(wrapper.find('[data-testid="acc-verify-sent"]').exists()).toBe(false);
	});

	it("sends the form with the authority evidence, then says where the link went", async () => {
		const upload = vi.fn(async () => REGISTERED);
		const call = vi.fn(async () => account("VERIFY"));
		const wrapper = mountWith(RegisterScreen, { initial: NEW_ACCOUNT }, portalFor({ upload, call }));
		const file = new File(["%PDF-1.4"], "mary-wanjiku-signing-authority.pdf", { type: "application/pdf" });
		const input = wrapper.get('[data-testid="acc-authority"]');
		Object.defineProperty(input.element, "files", { value: [file] });
		await input.trigger("change");
		expect(wrapper.get('[data-testid="acc-authority-name"]').text()).toBe("mary-wanjiku-signing-authority.pdf");
		await wrapper.get('[data-testid="acc-create"]').trigger("click");
		await flushPromises();
		const [method, fields, files] = upload.mock.calls[0];
		expect(method).toBe("kentender_suppliers.supplier_accounts.api.register_supplier_organisation");
		expect(files.authority_evidence).toBe(file);
		expect(fields.idempotency_key).toMatch(/^acc-register-/);
		expect(wrapper.get('[data-testid="acc-verify-sent"]').text()).toContain("We sent a verification link to tenders@afyadigital.example. Verify it before starting a bid.");
		expect(wrapper.text()).toContain("Pending verification");
		expect(wrapper.text()).not.toContain("Active");
	});

	it("tells the signed-in person to use the organisation's email, not their own", () => {
		const wrapper = mountWith(RegisterScreen, { initial: NEW_ACCOUNT }, portalFor());
		expect(wrapper.text()).toContain("You are signed in as Mary Wanjiku. Enter the organisation’s official email, not your personal sign-in email.");
		expect(wrapper.text()).toContain("It does not prequalify or approve the organisation for a Tender.");
	});
});

describe("Account", () => {
	it("shows the read's status, facts, people, evidence and notice contacts", () => {
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor());
		expect(wrapper.get('[data-testid="acc-status"]').text()).toBe("Active");
		expect(wrapper.text()).toContain("PVT-9X7K2M");
		expect(wrapper.get('[data-testid="acc-people"]').text()).toContain("Bid Coordinator");
		expect(wrapper.get('[data-testid="acc-evidence"]').text()).toContain("AGPO-Y-2026-04172");
		expect(wrapper.get('[data-testid="acc-contacts"]').text()).toContain("Verified");
		expect(wrapper.find('[data-testid="acc-add-person"]').exists()).toBe(true);
	});

	it("opens Edit organisation on the missing field from the blocked next step and saves against the read version", async () => {
		const call = vi.fn(async (method) => (method.endsWith("update_supplier_organisation") ? { ok: true, organisation: "ORG-AFYA", record_version: 4, verification_sent_to: "" } : account()));
		const wrapper = mountWith(AccountScreen, { initial: account("ATTENTION") }, portalFor({ call }));
		expect(wrapper.find('[data-testid="acc-status"]').exists()).toBe(false);
		await wrapper.get('[data-fix="edit_organisation:official_phone"]').trigger("click");
		await nextTick();
		await nextTick();
		expect(document.activeElement).toBe(wrapper.get('[data-testid="acc-edit-official_phone"]').element);
		await wrapper.get('[data-testid="acc-edit-official_phone"]').setValue("+254 709 555 014");
		await wrapper.get('[data-testid="acc-edit-save"]').trigger("click");
		await flushPromises();
		const [, args] = call.mock.calls.find(([m]) => m.endsWith("update_supplier_organisation"));
		expect(JSON.parse(args.values).official_phone).toBe("+254 709 555 014");
		expect(args.expected_version).toBe(3);
		expect(wrapper.find('[data-testid="acc-edit-dialog"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="acc-status"]').text()).toBe("Active");
	});

	it("keeps an edit refusal in the dialog", async () => {
		const call = vi.fn(async () => ({ ok: false, errors: { official_email: "Enter the organisation's official email." } }));
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor({ call }));
		await wrapper.get('[data-testid="acc-edit"]').trigger("click");
		await wrapper.get('[data-testid="acc-edit-official_email"]').setValue("not-an-email");
		await wrapper.get('[data-testid="acc-edit-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="acc-edit-dialog"]').text()).toContain("Enter the organisation's official email.");
		expect(wrapper.get('[data-testid="acc-edit-official_email"]').element.value).toBe("not-an-email");
	});

	it("resends the verification link while pending", async () => {
		const call = vi.fn(async () => ({ ok: true, sent: true, sent_to: "tenders@afyadigital.example", message: "" }));
		const wrapper = mountWith(AccountScreen, { initial: account("VERIFY") }, portalFor({ call }));
		expect(wrapper.get('[data-testid="acc-status"]').text()).toBe("Pending verification");
		await wrapper.get('[data-testid="acc-resend"]').trigger("click");
		await flushPromises();
		expect(call.mock.calls[0][0]).toBe("kentender_suppliers.supplier_accounts.api.send_account_verification");
		expect(wrapper.get('[data-testid="acc-message"]').text()).toBe("We sent a new verification link to tenders@afyadigital.example.");
	});

	it("offers a suspended Account no action beyond its receipts and support", () => {
		const wrapper = mountWith(AccountScreen, { initial: account("SUSPENDED") }, portalFor());
		expect(wrapper.get('[data-testid="acc-status"]').text()).toBe("Account suspended");
		for (const id of ["acc-edit", "acc-resend", "acc-add-person", "acc-add-evidence"]) expect(wrapper.find(`[data-testid="${id}"]`).exists(), id).toBe(false);
		expect(wrapper.get('[data-testid="acc-links"]').text()).toContain("View receipts");
		expect(wrapper.text()).toContain("Amina Yusuf is reviewing suspended access.");
	});

	it("draws labelled cards at the narrow frame", () => {
		globalThis.__narrow = true;
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor());
		expect(wrapper.find('[data-testid="acc-people"]').exists()).toBe(false);
		expect(wrapper.get('[data-testid="acc-people-cards"]').text()).toContain("Supplier Representative");
		expect(wrapper.get('[data-testid="acc-evidence-cards"]').findAll(".acc-card")).toHaveLength(3);
	});

	it("masks another organisation's Account as not found", async () => {
		const call = vi.fn(async () => ({ outcome: "NOT_FOUND", heading: "Account not found" }));
		const wrapper = mountWith(AccountScreen, { initial: null }, portalFor({ call, query: { organisation: "ORG-OTHER" } }));
		await flushPromises();
		expect(call.mock.calls[0][1]).toEqual({ organisation: "ORG-OTHER" });
		expect(wrapper.get('[data-testid="acc-not-found"]').text()).toContain("Account not found");
	});

	it("sends a person with no Account to the registration form", async () => {
		const call = vi.fn(async () => ({ outcome: "OK", state: "no_account", organisations: [] }));
		const wrapper = mountWith(AccountScreen, { initial: null }, portalFor({ call }));
		await flushPromises();
		expect(wrapper.emitted("no-account")).toHaveLength(1);
	});

	it("names a load failure in place with Try again", async () => {
		const call = vi.fn(async () => {
			throw new Error("The server could not be reached.");
		});
		const wrapper = mountWith(AccountScreen, { initial: null }, portalFor({ call }));
		await flushPromises();
		expect(wrapper.text()).toContain("The server could not be reached.");
		expect(wrapper.text()).toContain("Try again");
	});
});

describe("Business profile", () => {
	const profileCall = (reply) => vi.fn(async (method) => (method.endsWith("update_business_profile") ? reply : account()));

	it("shows the standing facts and the owners table, and offers the editor", async () => {
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor());
		expect(wrapper.get('[data-testid="acc-profile-fact-business_structure"]').text()).toBe("Registered company");
		expect(wrapper.get('[data-testid="acc-profile-fact-nominal_capital"]').text()).toBe("5000000.00");
		expect(wrapper.get('[data-testid="acc-profile-directors-table"]').text()).toContain("John Kamau");
		expect(wrapper.find('[data-testid="acc-profile-missing"]').exists()).toBe(false);
	});

	it("shows the owners as cards when narrow", () => {
		globalThis.__narrow = true;
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor());
		expect(wrapper.find("table.acc-owners").exists()).toBe(false);
		expect(wrapper.get('[data-testid="acc-profile-directors-cards"]').text()).toContain("John Kamau");
	});

	it("says what is missing on an empty profile", async () => {
		const read = { ...account(), business_profile: businessProfile(true) };
		const wrapper = mountWith(AccountScreen, { initial: read }, portalFor());
		expect(wrapper.get('[data-testid="acc-profile-missing"]').text()).toContain("choose the business structure");
	});

	it("names a refused table and a refused cell in place and keeps what was entered", async () => {
		const reply = { ok: false, code: "BDS_FIELD_INVALID", errors: { directors: "Shares owned must add up to 100; they add up to 60.00.", "directors.0.shares": "Enter a number." } };
		const call = profileCall(reply);
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor({ call }));
		await wrapper.get('[data-testid="acc-edit-profile"]').trigger("click");
		await wrapper.get('[data-testid="acc-profile-directors-0-shares"]').setValue("sixty");
		await wrapper.get('[data-testid="acc-profile-save"]').trigger("click");
		await flushPromises();
		expect(wrapper.get('[data-testid="acc-profile-directors-error"]').text()).toContain("add up to 100");
		expect(wrapper.get('[data-testid="acc-profile-directors-0-shares"]').attributes("aria-invalid")).toBe("true");
		expect(wrapper.get('[data-testid="acc-profile-directors-0-shares"]').element.value).toBe("sixty");
		expect(wrapper.get('[data-testid="acc-profile-dialog"]').exists()).toBe(true);
	});

	it("sends the profile against the version the page read, and closes when saved", async () => {
		const call = profileCall({ ok: true, organisation: "ORG-AFYA", record_version: 3, missing: [] });
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor({ call }));
		await wrapper.get('[data-testid="acc-edit-profile"]').trigger("click");
		await wrapper.get('[data-testid="acc-profile-save"]').trigger("click");
		await flushPromises();
		const sent = call.mock.calls.find(([m]) => m.endsWith("update_business_profile"))[1];
		expect(sent.expected_version).toBe(2);
		expect(sent.idempotency_key).toMatch(/^acc-profile-/);
		expect(JSON.parse(sent.values).directors).toHaveLength(2);
		expect(wrapper.find('[data-testid="acc-profile-dialog"]').exists()).toBe(false);
	});

	it("takes at most ten rows and shows the shares added up", async () => {
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor());
		await wrapper.get('[data-testid="acc-edit-profile"]').trigger("click");
		expect(wrapper.get('[data-testid="acc-profile-directors-total"]').text()).toContain("100");
		for (let i = 0; i < 8; i += 1) await wrapper.get('[data-testid="acc-profile-directors-add"]').trigger("click");
		expect(wrapper.findAll('[data-testid="acc-profile-directors-row"]')).toHaveLength(10);
		expect(wrapper.get('[data-testid="acc-profile-directors-add"]').attributes("disabled")).toBeDefined();
	});

	it("shows only the details of the chosen structure", async () => {
		const wrapper = mountWith(AccountScreen, { initial: account() }, portalFor());
		await wrapper.get('[data-testid="acc-edit-profile"]').trigger("click");
		expect(wrapper.find('[data-testid="acc-profile-nominal_capital"]').exists()).toBe(true);
		await wrapper.get('[data-testid="acc-profile-business_structure"]').setValue("Sole proprietor");
		expect(wrapper.find('[data-testid="acc-profile-nominal_capital"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="acc-profile-sole_proprietor_age"]').exists()).toBe(true);
		expect(wrapper.find('[data-testid="acc-profile-directors"]').exists()).toBe(false);
	});
});
