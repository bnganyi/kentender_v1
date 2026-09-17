// PLN-CHG-001 v1.18 (PLN18-306) — FinanceHistory component tests.
// U10-history: the two named evidence states and every review row, in
// order — a later Review never overwrites an earlier one's own outcome.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import FinanceHistory from "./FinanceHistory.vue";

const HISTORY = [
	{ review: "Review 1", basis: "MOH-BUD-2027-001, Version 1", outcome: "Confirmed", actor: "Josphat Mwangi", time_display: "4 Dec 2026" },
	{ review: "Review 2", basis: "Current revised Budget basis", outcome: "Awaiting confirmation", actor: "—", time_display: "—" },
];

function make(props = {}) {
	return mount(FinanceHistory, { props: { history: HISTORY, fundingEvidence: { state: "Awaiting confirmation", at_approval: { decision: "FND-1" } }, ...props } });
}

describe("FinanceHistory — U10-history", () => {
	it("renders the two evidence-state facts and every review row in order", () => {
		const w = make();
		expect(w.find(".kt-card-title").text()).toBe("Funding evidence history");
		const facts = w.findAll(".pln-fact");
		expect(facts.map((f) => f.get(".kt-label").text())).toEqual(["Funding evidence at approval", "Current funding confirmation"]);
		expect(facts[0].text()).toContain("Confirmed");
		expect(facts[1].text()).toContain("Awaiting confirmation");
		expect(w.findAll("thead th").map((th) => th.text())).toEqual(["Review", "Basis", "Outcome", "Actor", "Time"]);
		const rows = w.findAll("tbody tr");
		expect(rows).toHaveLength(2);
		expect(rows[0].findAll("td").map((td) => td.text())).toEqual(["Review 1", "MOH-BUD-2027-001, Version 1", "Confirmed", "Josphat Mwangi", "4 Dec 2026"]);
		expect(rows[1].findAll("td").map((td) => td.text())).toEqual(["Review 2", "Current revised Budget basis", "Awaiting confirmation", "—", "—"]);
	});

	it("shows 'Not yet confirmed' before any approval-time evidence exists", () => {
		const w = make({ fundingEvidence: { state: "Awaiting confirmation", at_approval: null } });
		expect(w.findAll(".pln-fact")[0].text()).toContain("Not yet confirmed");
	});
});
