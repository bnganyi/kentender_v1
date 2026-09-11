// REQ-DES-10 Authorised Requisition (§13.12) — header with handoff id,
// Planning-drawdown and Tender-status cards, the Budget-reservations table
// with real references, the complete-structured-package summary, the
// authorised-by line, the digest, and Revoke — hidden once consumed.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import AuthorisedScreen from "./AuthorisedScreen.vue";

const HANDOFF = {
	requisition: { requisition: "PRQ-001", requisition_reference: "REQ-MOH-2027-033-001", plan_item_id: "PPI-MOH-2027-033" },
	handoff: "HND-MOH-2027-033-001",
	handoff_digest: "a71e0c4d9f2b",
	payload: {
		requirement_title: "Clinical training and deployment laptops for digital health rollout",
		drawdown_lines: [
			{ source_line_id: "SRC-MOH-033-001" },
			{ source_line_id: "SRC-MOH-033-002" },
		],
	},
	drawdown_display: [
		{ reservation_label: "RSV-MOH-2027-033-001", organisation_unit_label: "Human Resources Management and Development", requested_value: 20_000_000, budget_line_label: "MOH-BL-HWD-2027" },
		{ reservation_label: "RSV-MOH-2027-033-002", organisation_unit_label: "Digital Health", requested_value: 30_000_000, budget_line_label: "MOH-BL-HWD-2027" },
	],
	package_summary: { items: 2, technical_requirements: 11, acceptance_requirements: 5 },
	authorised_by: { name: "Charles Mutiso", role: "Head of Procurement Function", decided_at: "2027-03-15 10:00:00" },
	consumption: { tender: "", tender_version: "", template_key: "", template_version: "", consumed_at: "" },
	can_revoke: true,
};

function make(overrides = {}) {
	return mount(AuthorisedScreen, { props: { handoff: { ...HANDOFF, ...overrides }, pending: false } });
}

describe("AuthorisedScreen — REQ-DES-10", () => {
	it("renders the exact header with the handoff id and status", () => {
		const w = make();
		expect(w.find(".kt-eyebrow").text()).toBe("AUTHORISED REQUISITION");
		expect(w.find(".kt-status").text()).toBe("Authorised for Tender Preparation");
		expect(w.text()).toContain("Handoff HND-MOH-2027-033-001");
	});

	it("renders the Planning-drawdown and Tender-status cards", () => {
		const w = make();
		expect(w.text()).toContain("PPI-MOH-2027-033");
		expect(w.text()).toContain("SRC-MOH-033-001 · SRC-MOH-033-002");
		expect(w.text()).toContain("Not yet consumed");
	});

	it("renders the Budget-reservations table with real references, never internal docnames", () => {
		const w = make();
		const rows = w.findAll('[data-testid="req-reservations-table"] tbody tr');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("RSV-MOH-2027-033-001");
		expect(rows[0].text()).toContain("Human Resources Management and Development");
		expect(rows[0].text()).toContain("KES 20,000,000.00");
		expect(rows[0].text()).toContain("MOH-BL-HWD-2027");
	});

	it("renders the complete-structured-package summary and the authorised-by/digest lines", () => {
		const w = make();
		expect(w.text()).toContain("2 items");
		expect(w.text()).toContain("11 rows");
		expect(w.text()).toContain("5 rows");
		expect(w.text()).toContain("Authorised by Charles Mutiso, Head of Procurement Function · 2027-03-15 10:00:00");
		expect(w.text()).toContain("a71e0c4d9f2b");
	});

	it("uses singular grammar for a single-row package summary", () => {
		// found live: "1 rows" on a small real requisition — the artboard's
		// own fixture is always >1 so this never surfaced there.
		const w = make({ package_summary: { items: 1, technical_requirements: 1, acceptance_requirements: 1 } });
		expect(w.text()).toContain("1 item");
		expect(w.text()).not.toContain("1 items");
		expect(w.text()).toContain("1 row");
		expect(w.text()).not.toContain("1 rows");
	});

	it("shows Revoke when can_revoke is true and emits on click", async () => {
		const w = make();
		await w.find('[data-testid="req-revoke"]').trigger("click");
		expect(w.emitted("revoke")).toBeTruthy();
	});

	it("hides Revoke entirely (never merely disables it) once can_revoke is false", () => {
		const w = make({ can_revoke: false });
		expect(w.find('[data-testid="req-revoke"]').exists()).toBe(false);
	});

	it("shows the Consumed status and hides Open Tender Preparation once consumed", () => {
		const w = make({
			consumption: { tender: "TND-MOH-2027-033", tender_version: "TND-MOH-2027-033-V1", template_key: "IT Equipment — Open Tender", template_version: "v1.1", consumed_at: "2027-03-20 09:00:00" },
			can_revoke: false,
		});
		expect(w.text()).toContain("Consumed by TND-MOH-2027-033 · IT Equipment — Open Tender v1.1");
		expect(w.find('[data-testid="req-open-tender"]').exists()).toBe(false);
		expect(w.find('[data-testid="req-revoke"]').exists()).toBe(false);
	});

	it("shows Open Tender Preparation only while unconsumed and emits open-tender", async () => {
		const w = make();
		await w.find('[data-testid="req-open-tender"]').trigger("click");
		expect(w.emitted("open-tender")).toBeTruthy();
	});
});
