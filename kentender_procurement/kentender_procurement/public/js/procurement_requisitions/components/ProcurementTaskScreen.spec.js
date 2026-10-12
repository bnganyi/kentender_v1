// REQ-DES-08 — the Procurement checks table shows what was checked beside what it found. The rows are the
// server's own shape (`compatibility.Check.as_dict`: test, check, ok, result, failure, code); a column that
// read the wrong key came out blank while every test still passed on a fixture with the same mistake.
import { beforeEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";

import ProcurementTaskScreen from "./ProcurementTaskScreen.vue";
import { context, procurementTask } from "./fixtures.js";

beforeEach(() => window.sessionStorage.clear());

describe("ProcurementTaskScreen — Procurement checks", () => {
	it("names every check in the first column and its result in the second", async () => {
		const { global } = context();
		const view = procurementTask();
		view.checks = { ...view.checks, open: true };
		const w = mount(ProcurementTaskScreen, { props: { view }, global });
		const rows = w.findAll('[data-testid="req-checks"] tbody tr');
		expect(rows).toHaveLength(9);
		for (const row of rows) {
			const cells = row.findAll("td");
			expect(cells[0].text(), "the check is named").not.toBe("");
			expect(cells[1].text(), "its result is shown").not.toBe("");
		}
		expect(rows[0].findAll("td").map((c) => c.text())).toEqual(["Procurement category", "Goods"]);
	});

	it("a failed check says what failed, still beside its name", async () => {
		const { global } = context();
		const view = procurementTask();
		view.checks = { summary: "1 check failed", open: true, rows: [{ test: "currency", check: "Currency", ok: false, result: "USD", failure: "Currency USD is not KES.", code: "REQ_COMPATIBILITY_FAILED" }] };
		const w = mount(ProcurementTaskScreen, { props: { view }, global });
		expect(w.findAll('[data-testid="req-checks"] tbody tr td').map((c) => c.text())).toEqual(["Currency", "Currency USD is not KES."]);
	});

	it("Record details: a list of references breaks between references, one per line, and every fact has a label and a value", async () => {
		const { global } = context();
		const view = procurementTask();
		view.record_details = [{ label: "Requisition reference", value: "REQ-MOH-2027-003-001" }, { label: "Reservation references", value: "RSV-MOH-2027-033-001; RSV-MOH-2027-033-002" }];
		const w = mount(ProcurementTaskScreen, { props: { view }, global });
		const details = w.find('[data-testid="req-record-details"]');
		details.element.open = true;
		details.element.dispatchEvent(new Event("toggle"));
		await w.vm.$nextTick();
		const facts = w.findAll('[data-testid="req-record-details"] .req-facts > div');
		expect(facts).toHaveLength(2);
		expect(facts[0].findAll(".req-fact-line").map((l) => l.text())).toEqual(["REQ-MOH-2027-003-001"]);
		expect(facts[1].findAll(".req-fact-line").map((l) => l.text())).toEqual(["RSV-MOH-2027-033-001", "RSV-MOH-2027-033-002"]);
	});
});
