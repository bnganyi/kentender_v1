// Tender-security receipts (BDS-CHG-001 v0.8 owner decisions OD-G/OD-H):
// the recorder sees their own intakes and the published Tender's own
// security facts, never a bid; bad input is named field by field and kept;
// a retried click reuses one request key. Server payloads are the fixtures;
// no component derives a match, status or permission of its own.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { flushPromises, mount } from "@vue/test-utils";
import { ref } from "vue";

const api = vi.hoisted(() => ({ listIntakes: vi.fn(), getRequirement: vi.fn(), recordIntake: vi.fn() }));
const route = vi.hoisted(() => ({ hash: null, goHash: null }));
vi.mock("./data/api.js", () => api);
vi.mock("../tnd_shared/composables/usePageRail.js", () => ({ usePageRail: vi.fn() }));
vi.mock("./composables/useRouteState.js", () => ({
	useRouteState: () => {
		route.hash = ref("");
		route.goHash = vi.fn((fragment) => (route.hash.value = fragment));
		return { epoch: ref(0), hash: route.hash, goHash: route.goHash };
	},
}));

import IntakeDialog from "./IntakeDialog.vue";
import TenderSecurityReceipts from "./TenderSecurityReceipts.vue";

const g = { global: { mocks: { __: (s) => s } } };
const BID_WORDS = /\b(BID-|ARR-|bid status|Matched|Candidate|supplier|Draft)\b/i;
const ROW = {
	status: "Current", corrected_by: "", corrects: "", amount_value: "500000.00", currency: "KES", received_at_value: "2027-05-19T09:00",
	intake_reference: "TSI-4F2A9C01B7", tender_reference: "TND-MOH-2027-002", instrument_type: "Demand Bank Guarantee", issuer: "KCB Bank Kenya",
	instrument_reference: "KCB/TG/2027/8841", amount: "KES 500,000.00", received_at: "19 May 2027, 09:00 EAT", deadline_class: "Before deadline", recorded_at: "19 May 2027, 09:05 EAT", notes: "",
};
const REQUIREMENT = {
	outcome: "OK", found: true, required: true, tender_reference: "TND-MOH-2027-002", permitted_forms: ["Demand Bank Guarantee"], currency: "KES",
	required_amount: "KES 500,000.00", deadline: "12 Jun 2027, 11:00 EAT",
};

beforeEach(() => {
	vi.clearAllMocks();
	api.getRequirement.mockResolvedValue(REQUIREMENT);
});

describe("TenderSecurityReceipts", () => {
	it("lists the recorder's own intakes with no bid fact", async () => {
		api.listIntakes.mockResolvedValue({ outcome: "OK", rows: [ROW], empty_text: "You have not recorded any tender-security originals yet." });
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		expect(w.find("h1").text()).toBe("Tender-security receipts");
		expect(w.findAll('[data-testid="tsr-row"]')).toHaveLength(1);
		expect(w.find("thead").text()).toBe("Intake referenceTenderInstrumentAmountReceivedRecordedActions");
		expect(w.text()).toContain("Before deadline");
		expect(w.text()).not.toMatch(BID_WORDS);
	});

	it("shows the empty state, then the filtered empty state with Clear filters", async () => {
		api.listIntakes.mockResolvedValue({ outcome: "OK", rows: [], empty_text: "You have not recorded any tender-security originals yet." });
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		expect(w.find('[data-testid="tsr-empty"]').text()).toBe("You have not recorded any tender-security originals yet.");
		expect(w.find('[data-testid="tsr-clear-filters"]').exists()).toBe(false);
		await w.find('[data-testid="tsr-filter-tender"]').setValue("TND-NONE");
		await w.find('[data-testid="tsr-filter-tender"]').trigger("change");
		await flushPromises();
		expect(route.goHash).toHaveBeenLastCalledWith("tender=TND-NONE", { replace: true });
		expect(api.listIntakes).toHaveBeenLastCalledWith({ tender: "TND-NONE" });
		expect(w.find('[data-testid="tsr-empty"]').text()).toBe("No receipts match this Tender reference.");
		await w.find('[data-testid="tsr-clear-filters"]').trigger("click");
		await flushPromises();
		expect(route.goHash).toHaveBeenLastCalledWith("", { replace: true });
		expect(w.find('[data-testid="tsr-filter-tender"]').element.value).toBe("");
	});

	it("shows Forbidden as a state with no record action", async () => {
		api.listIntakes.mockResolvedValue({ outcome: "FORBIDDEN", heading: "You do not have access to tender-security receipts", text: "Only the Head of Procurement Function records physical tender-security originals." });
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		expect(w.find('[data-testid="tsr-forbidden"]').text()).toContain("Only the Head of Procurement Function records physical tender-security originals.");
		expect(w.find('[data-testid="tsr-record"]').exists()).toBe(false);
	});

	it("shows a read failure with Try again and never stale rows", async () => {
		api.listIntakes.mockRejectedValueOnce(new Error("Server error"));
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		expect(w.find('[data-testid="tsr-failure"]').exists()).toBe(true);
		expect(w.find('[data-testid="tsr-table"]').exists()).toBe(false);
		api.listIntakes.mockResolvedValue({ outcome: "OK", rows: [ROW] });
		await w.find('[data-testid="tsr-retry"]').trigger("click");
		await flushPromises();
		expect(w.findAll('[data-testid="tsr-row"]')).toHaveLength(1);
	});

	it("records a receipt, confirms it with the intake reference and reloads the list", async () => {
		api.listIntakes.mockResolvedValueOnce({ outcome: "OK", rows: [] }).mockResolvedValue({ outcome: "OK", rows: [ROW] });
		api.recordIntake.mockResolvedValue({ ok: true, ...ROW });
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		await w.find('[data-testid="tsr-record"]').trigger("click");
		await w.findComponent(IntakeDialog).vm.$emit("submit", { values: { tender_reference: "TND-MOH-2027-002" }, key: "tsi-k" });
		await flushPromises();
		expect(w.findComponent(IntakeDialog).exists()).toBe(false);
		expect(w.find('[data-testid="tsr-recorded"]').text()).toBe("Receipt recorded. Intake reference TSI-4F2A9C01B7.");
		expect(w.findAll('[data-testid="tsr-row"]')).toHaveLength(1);
	});

	it("keeps the dialog open and names each field the server refused", async () => {
		api.listIntakes.mockResolvedValue({ outcome: "OK", rows: [] });
		api.recordIntake.mockResolvedValue({ ok: false, code: "BDS_FIELD_INVALID", errors: { received_at: "The time received cannot be in the future.", confirmed: "Confirm that the original was received as recorded." } });
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		await w.find('[data-testid="tsr-record"]').trigger("click");
		await w.findComponent(IntakeDialog).vm.$emit("submit", { values: {}, key: "tsi-k" });
		await flushPromises();
		const dialog = w.findComponent(IntakeDialog);
		expect(dialog.exists()).toBe(true);
		expect(dialog.text()).toContain("The time received cannot be in the future.");
		expect(dialog.text()).toContain("Confirm that the original was received as recorded.");
		expect(w.find('[data-testid="tsr-recorded"]').exists()).toBe(false);
	});
});

describe("IntakeDialog", () => {
	it("looks the Tender up and shows only its published security facts", async () => {
		const w = mount(IntakeDialog, { props: { initialTender: "TND-MOH-2027-002" }, ...g });
		await flushPromises();
		expect(api.getRequirement).toHaveBeenCalledWith("TND-MOH-2027-002");
		expect(w.find('[data-testid="tsr-d-requirement"]').text()).toBe("Required: KES 500,000.00 as Demand Bank Guarantee. Submission deadline 12 Jun 2027, 11:00 EAT.");
		expect(w.findAll('[data-testid="tsr-d-type"] option:not([disabled])').map((o) => o.text())).toEqual(["Demand Bank Guarantee"]);
		expect(w.find('[data-testid="tsr-d-currency"]').element.value).toBe("KES");
		expect(w.text()).not.toMatch(BID_WORDS);
	});

	it("says plainly when a reference is not a published Tender", async () => {
		api.getRequirement.mockResolvedValue({ outcome: "OK", found: false, text: "No published Tender has this reference." });
		const w = mount(IntakeDialog, g);
		await w.find('[data-testid="tsr-d-tender"]').setValue("TND-NOPE");
		await w.find('[data-testid="tsr-d-tender"]').trigger("change");
		await flushPromises();
		expect(w.find('[data-testid="tsr-d-requirement"]').text()).toBe("No published Tender has this reference.");
	});

	it("submits the entered details with seconds added and the same key on a retry", async () => {
		const w = mount(IntakeDialog, { props: { initialTender: "TND-MOH-2027-002" }, ...g });
		await flushPromises();
		await w.find('[data-testid="tsr-d-type"]').setValue("Demand Bank Guarantee");
		await w.find('[data-testid="tsr-d-issuer"]').setValue("KCB Bank Kenya");
		await w.find('[data-testid="tsr-d-reference"]').setValue("KCB/TG/2027/8841");
		await w.find('[data-testid="tsr-d-amount"]').setValue("500000.00");
		await w.find('[data-testid="tsr-d-received"]').setValue("2027-05-19T09:00");
		await w.find('[data-testid="tsr-d-confirm"]').setValue(true);
		await w.find('[data-testid="tsr-d-submit"]').trigger("click");
		await w.find('[data-testid="tsr-d-submit"]').trigger("click");
		const [first, second] = w.emitted("submit").map((e) => e[0]);
		expect(first.values).toEqual({
			tender_reference: "TND-MOH-2027-002", instrument_type: "Demand Bank Guarantee", issuer: "KCB Bank Kenya", instrument_reference: "KCB/TG/2027/8841",
			amount: "500000.00", currency: "KES", received_at: "2027-05-19 09:00:00", notes: "", confirmed: true,
		});
		expect(second.key).toBe(first.key);
	});

	it("shows each field error inline and keeps what was entered", async () => {
		const w = mount(IntakeDialog, { props: { errors: { issuer: "Enter the issuing bank or insurer.", amount: "Enter the amount on the instrument, for example 500000.00." } }, ...g });
		await w.find('[data-testid="tsr-d-reference"]').setValue("REF-1");
		expect(w.findAll(".kt-field-error").map((e) => e.text())).toEqual(["Enter the issuing bank or insurer.", "Enter the amount on the instrument, for example 500000.00."]);
		expect(w.find('[data-testid="tsr-d-issuer"]').attributes("aria-invalid")).toBe("true");
		expect(w.find('[data-testid="tsr-d-reference"]').element.value).toBe("REF-1");
	});
});


describe("Correcting a receipt", () => {
	it("offers Correct only on a current receipt and shows the link both ways", async () => {
		const corrected = { ...ROW, intake_reference: "TSI-AAAAAAAAAA", status: "Corrected", corrected_by: "TSI-BBBBBBBBBB" };
		const correction = { ...ROW, intake_reference: "TSI-BBBBBBBBBB", corrects: "TSI-AAAAAAAAAA" };
		api.listIntakes.mockResolvedValue({ outcome: "OK", rows: [correction, corrected] });
		const w = mount(TenderSecurityReceipts, g);
		await flushPromises();
		expect(w.findAll('[data-testid="tsr-correct"]')).toHaveLength(1);
		expect(w.find('[data-testid="tsr-corrects"]').text()).toBe("Corrects TSI-AAAAAAAAAA");
		expect(w.find('[data-testid="tsr-corrected-by"]').text()).toBe("Corrected by TSI-BBBBBBBBBB");
	});

	it("opens the dialog filled from the receipt and sends the correction with its reason", async () => {
		const w = mount(IntakeDialog, { props: { correcting: ROW }, ...g });
		await flushPromises();
		expect(w.find("#tsr-d-title").text()).toBe(`Correct receipt ${ROW.intake_reference}`);
		expect(w.find('[data-testid="tsr-d-reference"]').element.value).toBe(ROW.instrument_reference);
		expect(w.find('[data-testid="tsr-d-amount"]').element.value).toBe("500000.00");
		await w.find('[data-testid="tsr-d-reason"]').setValue("The guarantee number was typed wrongly.");
		await w.find('[data-testid="tsr-d-confirm"]').setValue(true);
		await w.find('[data-testid="tsr-d-submit"]').trigger("click");
		const sent = w.emitted("submit")[0][0].values;
		expect((({ corrects, correction_reason, received_at, instrument_reference }) => ({ corrects, correction_reason, received_at, instrument_reference }))(sent)).toEqual({
			corrects: ROW.intake_reference, correction_reason: "The guarantee number was typed wrongly.", received_at: "2027-05-19 09:00:00", instrument_reference: ROW.instrument_reference,
		});
		expect(w.find('[data-testid="tsr-d-submit"]').text()).toBe("Record correction");
	});
});
