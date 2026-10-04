// BDS-CHG-001 v0.8 §10.3 / §11.2 — the Tender overview's actions: Start bid
// opens "Who is bidding?" and sends one StartBid with the chosen notice
// email; a refusal names the field and keeps the entry; Ask a question names
// a too-short question in place and confirms a sent one; a Not found read
// hands the page to the not-found state.
import { afterEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

import { createCommandRunner, createScreenCache, createSequenceGuard } from "../../../../../../kentender_core/kentender_core/public/js/kt_portal/runtime.js";
import TenderOverviewScreen from "./TenderOverviewScreen.vue";
import { overview } from "./TenderOverviewScreen.fixtures.js";

function fakePortal(answers) {
	const route = ref({ path: "/tenders/TND-MOH-2027-033", segments: ["tenders", "TND-MOH-2027-033"], query: {} });
	return {
		call: vi.fn(async (method) => answers[method.split(".").pop()]),
		setTitle: vi.fn(), createSequenceGuard, createScreenCache, createCommandRunner: (vue, opts) => createCommandRunner(vue, opts),
		useRoute: () => ({ route, go: vi.fn(), epoch: ref(0) }),
	};
}
function render(initial, answers = {}) {
	const portal = fakePortal(answers);
	const wrapper = mount(TenderOverviewScreen, { props: { initial, reference: "TND-MOH-2027-033" }, attachTo: document.body, global: { provide: { portal }, config: { globalProperties: { __: globalThis.__ } } } });
	return { wrapper, portal };
}
afterEach(() => (document.body.innerHTML = ""));

describe("Start bid", () => {
	it("opens Who is bidding? and sends one StartBid with the organisation and notice email", async () => {
		const data = overview("JV-START");
		const { wrapper, portal } = render(data, { start_bid: { ok: true, bid_reference: "BID-1" }, get_tender_overview: overview("DRAFT") });
		await wrapper.find('[data-testid="bds-overview-action"]').trigger("click");
		expect(wrapper.find('[data-testid="bds-start-jv"]').exists()).toBe(true);
		await wrapper.find('[data-testid="bds-start-submit"]').trigger("click");
		await flushPromises();
		const [method, args, opts] = portal.call.mock.calls[0];
		expect([method.split(".").pop(), args.organisation, args.notice_contact_id, args.arrangement, opts.type]).toEqual(["start_bid", "ORG-KISIWA", "C1", { arrangement_type: "Single organisation" }, "POST"]);
		expect(args.idempotency_key).toMatch(/^bds-start-/);
		expect(wrapper.find('[data-testid="bds-start-dialog"]').exists()).toBe(false);
		expect(wrapper.find('[data-testid="bds-overview-action"]').text()).toBe("Continue bid");
	});

	it("keeps the joint-venture entry and names each refused field", async () => {
		const { wrapper } = render(overview("JV-START"), { start_bid: { ok: false, code: "BDS_ARRANGEMENT_INVALID", errors: { joint_venture_name: "Enter the joint-venture name.", "members.0": "No active supplier account has this country and registration number. The member must set up its own account first." } } });
		await wrapper.find('[data-testid="bds-overview-action"]').trigger("click");
		await wrapper.find('[data-testid="bds-start-jv"]').setValue(true);
		await wrapper.find('[data-testid="bds-member-reg-0"]').setValue("PVT-NONE");
		await wrapper.find('[data-testid="bds-start-submit"]').trigger("click");
		await flushPromises();
		expect(wrapper.findAll(".kt-field-error").map((e) => e.text())).toEqual(["Enter the joint-venture name.", "No active supplier account has this country and registration number. The member must set up its own account first."]);
		expect(wrapper.find('[data-testid="bds-member-reg-0"]').element.value).toBe("PVT-NONE");
	});
});

describe("Common states on the Tender page", () => {
	it("shows Format unsupported with Contact support when the bid format cannot be rendered", async () => {
		const data = overview("JV-START");
		data.start.support_href = "mailto:supplier.support@moh.example";
		const { wrapper, portal } = render(data);
		portal.call.mockRejectedValueOnce(Object.assign(new Error("This bid format is not available."), { code: "BDS_DEFINITION_UNSUPPORTED" }));
		await wrapper.find('[data-testid="bds-overview-action"]').trigger("click");
		await wrapper.find('[data-testid="bds-start-submit"]').trigger("click");
		await flushPromises();
		const state = wrapper.get('[data-testid="bds-state-format-unsupported"]');
		expect(state.get("strong").text()).toBe("This bid format is not available.");
		expect(state.text()).toContain("No bid was created for this Tender. Contact supplier support.");
		expect(state.get("a").attributes("href")).toBe("mailto:supplier.support@moh.example");
		expect(state.get("a").text()).toBe("Contact support");
		expect(wrapper.find('[data-testid="bds-start-submit"]').exists()).toBe(false);
	});

	it.each([
		["portal-information-new-visitor", "", "Starting a new bid is unavailable until support and legal information is restored.", "Try again"],
		["portal-information-draft", "/tenders/TND-MOH-2027-033/bid", "Your saved bid is still here.", "Continue saved bid"],
		["portal-information-submitted", "/account/receipts", "Your submitted bid and receipt remain available.", "View receipts"],
	])("names the %s variant while supplier information is unavailable", async (key, href, message, action) => {
		const data = overview("");
		data.state = { key, figures: {}, href, retry: false };
		const { wrapper, portal } = render(data, { get_tender_overview: data });
		const state = wrapper.get(`[data-testid="bds-state-${key}"]`);
		expect(state.get("strong").text()).toBe("Supplier support information is temporarily unavailable.");
		expect(state.text()).toContain(message);
		const control = state.get(href ? "a" : "button");
		expect(control.text()).toBe(action);
		if (href) expect(control.attributes("href")).toBe(href);
		else {
			await control.trigger("click");
			await flushPromises();
			expect(portal.call.mock.calls.map(([method]) => method.split(".").pop())).toEqual(["get_tender_overview"]);
		}
		expect(wrapper.find('[data-testid="bds-overview-documents"], .kt-region').exists()).toBe(true);
	});
});

describe("Ask a question", () => {
	it("names a too-short question in place and confirms a sent one", async () => {
		const { wrapper, portal } = render(overview("CANDIDATE-QUESTION"), { submit_tender_clarification: { ok: false, errors: { question: "Enter a question of 10 to 2,000 characters." } } });
		await wrapper.find('[data-testid="bds-ask-question"]').trigger("click");
		await wrapper.find('[data-testid="bds-question-text"]').setValue("Short");
		await wrapper.find('[data-testid="bds-question-send"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-question-dialog"] .kt-field-error').text()).toBe("Enter a question of 10 to 2,000 characters.");
		portal.call.mockImplementation(async (method) => (method.endsWith("submit_tender_clarification") ? { ok: true, received_at: "26 May 2027, 09:00 EAT" } : overview("CANDIDATE-QUESTION")));
		await wrapper.find('[data-testid="bds-question-text"]').setValue("May the two comparable contracts be from different customers?");
		await wrapper.find('[data-testid="bds-question-send"]').trigger("click");
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-question-sent"]').text()).toBe("Question received 26 May 2027, 09:00 EAT");
	});
});

describe("Not found", () => {
	it("hands the page over when the read says the Tender does not exist", async () => {
		const { wrapper } = render(null, { get_tender_overview: { outcome: "NOT_FOUND" } });
		await flushPromises();
		expect(wrapper.emitted("not-found")).toHaveLength(1);
	});

	describe("a bound Tender format", () => {
		it("superseded: says the Tender stays on its format and still offers Start bid", () => {
			const { wrapper } = render(overview("SUPERSEDED"));
			const notice = wrapper.get('[data-testid="bds-overview-release"]');
			expect([notice.classes().includes("is-warning"), notice.text()]).toEqual([false, expect.stringContaining("remains on its existing format")]);
			expect(wrapper.get('[data-testid="bds-overview-action"]').text()).toBe("Start bid");
		});

		it("withdrawn: keeps documents and the receipt, offers the signatory Withdraw bid and drops the status badge", () => {
			const { wrapper } = render(overview("WITHDRAWN-RELEASE"));
			expect(wrapper.get('[data-testid="bds-overview-release"]').classes()).toContain("is-warning");
			const buttons = wrapper.findAll(".kt-page-actions .kt-btn");
			expect(buttons.map((b) => b.text())).toEqual(["View Tender documents", "View receipt", "Withdraw bid"]);
			expect(buttons[0].attributes("href")).toBe("#bds-tender-documents");
			expect(buttons[2].classes()).toEqual(expect.arrayContaining(["kt-btn-primary", "kt-danger"]));
			expect(buttons[2].attributes("href")).toMatch(/\?action=withdraw$/);
			expect(wrapper.find('[data-testid="bds-overview-status"]').exists()).toBe(false);
			expect(wrapper.find("#bds-tender-documents").exists()).toBe(true);
			expect(wrapper.text()).not.toContain("Start bid");
		});
	});
});

describe("Dialog focus (BDS01-AC-088)", () => {
	it("moves focus into Who is bidding?, keeps Tab inside and returns it to Start bid on Escape", async () => {
		const { wrapper } = render(overview("JV-START"));
		const trigger = wrapper.get('[data-testid="bds-overview-action"]');
		trigger.element.focus();
		await trigger.trigger("click");
		await flushPromises();
		const dialog = wrapper.get('[data-testid="bds-start-dialog"]');
		expect(dialog.element.contains(document.activeElement)).toBe(true);
		const buttons = dialog.findAll("button");
		buttons.at(-1).element.focus();
		await dialog.trigger("keydown", { key: "Tab" });
		expect(dialog.element.contains(document.activeElement)).toBe(true);
		await dialog.trigger("keydown", { key: "Escape" });
		await flushPromises();
		expect(wrapper.find('[data-testid="bds-start-dialog"]').exists()).toBe(false);
		expect(document.activeElement).toBe(wrapper.get('[data-testid="bds-overview-action"]').element);
	});
});
