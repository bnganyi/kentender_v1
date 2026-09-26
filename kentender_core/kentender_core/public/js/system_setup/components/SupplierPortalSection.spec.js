// CFG-CHG-002 v0.16 §10.10A (C05) — the Supplier portal settings section.
import { flushPromises, mount } from "@vue/test-utils";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { globalMocks } from "./spec_helpers.js";

const api = vi.hoisted(() => ({ update: vi.fn() }));
vi.mock("../data/publicPortalApi.js", () => ({ publicPortalApi: api }));

import SupplierPortalSection from "./SupplierPortalSection.vue";

const COMPLETE = {
	supplier_support_email: "tendersupport@health.go.ke",
	supplier_support_phone: "+254 20 271 7077",
	supplier_support_hours: "Monday–Friday, 08:00–17:00 EAT",
	privacy_notice_url: "https://health.example.test/kentender/privacy",
	portal_terms_url: "https://health.example.test/kentender/terms",
	accessibility_statement_url: "https://health.example.test/kentender/accessibility",
};
const settings = (values = COMPLETE) => ({ values: { ...values }, record_version: 3, status: "Complete", missing: [] });
const tid = (id) => `[data-testid="${id}"]`;

describe("SupplierPortalSection", () => {
	beforeEach(() => vi.clearAllMocks());

	it("renders the complete settings with the spec's labels, helpers and one Save changes action", () => {
		const wrapper = mount(SupplierPortalSection, { props: { settings: settings() }, global: globalMocks() });
		expect(wrapper.find("h3").text()).toBe("Supplier portal");
		expect(wrapper.text()).toContain("Set the support contact and public information links shown to suppliers.");
		expect(wrapper.find(tid("kt-portal-info")).text()).toBe("These details appear on public Tender and bid pages. They do not change a Tender, candidate notice or submission status.");
		expect(wrapper.findAll("h4").map((h) => h.text())).toEqual(["Supplier support", "Public information"]);
		expect(wrapper.findAll("label").map((l) => l.text())).toEqual([
			"Support email", "Support phone (optional)", "Support hours (optional)",
			"Privacy and data use", "Terms of portal use", "Accessibility",
		]);
		expect(wrapper.text()).toContain("Support hours do not extend a procurement deadline.");
		expect(wrapper.findAll('[data-testid^="kt-portal-open-"]')).toHaveLength(3);
		expect(wrapper.find(tid("kt-portal-incomplete")).exists()).toBe(false);
		const buttons = wrapper.findAll("button").map((b) => b.text());
		expect(buttons.filter((t) => t !== "Open link")).toEqual(["Save changes"]);
		expect(wrapper.text()).not.toMatch(/Publish|Approve|Preview website|Enable bid submission/);
	});

	it("the incomplete variant keeps every value, names the field and withholds Save", async () => {
		const wrapper = mount(SupplierPortalSection, { props: { settings: settings({ ...COMPLETE, privacy_notice_url: "" }) }, global: globalMocks() });
		expect(wrapper.find(tid("kt-portal-incomplete")).text()).toBe("Complete the supplier support and public-information links before suppliers start or submit bids.");
		expect(wrapper.find(tid("kt-portal-privacy_notice_url-error")).text()).toBe("Enter a complete HTTPS address for Privacy and data use.");
		expect(wrapper.find(tid("kt-portal-open-privacy_notice_url")).exists()).toBe(false);
		expect(wrapper.find(tid("kt-portal-supplier_support_email")).element.value).toBe(COMPLETE.supplier_support_email);
		expect(wrapper.find(tid("kt-portal-save")).attributes("disabled")).toBeDefined();
	});

	it("an http address is invalid and has no Open link", async () => {
		const wrapper = mount(SupplierPortalSection, { props: { settings: settings() }, global: globalMocks() });
		await wrapper.find(tid("kt-portal-portal_terms_url")).setValue("http://example.test/terms");
		expect(wrapper.find(tid("kt-portal-portal_terms_url-error")).text()).toBe("Enter a complete HTTPS address for Terms of portal use.");
		expect(wrapper.find(tid("kt-portal-open-portal_terms_url")).exists()).toBe(false);
	});

	it("saves once with the current version and shows the saved confirmation", async () => {
		api.update.mockResolvedValue({ ok: true, record_version: 4 });
		const wrapper = mount(SupplierPortalSection, { props: { settings: settings() }, global: globalMocks() });
		await wrapper.find(tid("kt-portal-supplier_support_hours")).setValue("Weekdays 08:00–17:00 EAT");
		await wrapper.find(tid("kt-portal-save")).trigger("click");
		await flushPromises();
		expect(api.update).toHaveBeenCalledTimes(1);
		expect(api.update.mock.calls[0][0].supplier_support_hours).toBe("Weekdays 08:00–17:00 EAT");
		expect(api.update.mock.calls[0][1]).toBe(3);
		expect(wrapper.find(tid("kt-portal-saved")).text()).toContain("Supplier portal settings saved.");
		expect(wrapper.find(tid("kt-portal-saved")).text()).toContain("Used by Tenders and Bid Submission");
		expect(wrapper.emitted("saved")).toBeTruthy();
	});

	it("binds server field errors inline and keeps the entered values", async () => {
		api.update.mockResolvedValue({ ok: false, errors: { supplier_support_phone: "Enter a phone number using digits, spaces and an optional leading +." } });
		const wrapper = mount(SupplierPortalSection, { props: { settings: settings() }, global: globalMocks() });
		await wrapper.find(tid("kt-portal-supplier_support_phone")).setValue("call us");
		await wrapper.find(tid("kt-portal-save")).trigger("click");
		await flushPromises();
		expect(wrapper.find(tid("kt-portal-supplier_support_phone-error")).text()).toBe("Enter a phone number using digits, spaces and an optional leading +.");
		expect(wrapper.find(tid("kt-portal-supplier_support_phone")).element.value).toBe("call us");
		expect(wrapper.find(tid("kt-portal-saved")).exists()).toBe(false);
	});
});
