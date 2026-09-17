// PLN-CHG-001 v1.18 (PLN18-307) — GovernanceHistory component tests.
// U11-decisions: every stage's row, in order — the open stage reads
// Awaiting decision, never blank or overwritten by an earlier stage.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import GovernanceHistory from "./GovernanceHistory.vue";

const HISTORY = [
	{ stage: "Finance", actor: "Josphat Mwangi", capacity: "Finance Confirmation Officer", outcome: "Confirmed", date_display: "4 Dec 2026, 10:00" },
	{ stage: "Preparation", actor: "Charles Mutiso", capacity: "Head of Procurement Function", outcome: "Signed and submitted", date_display: "7 Dec 2026, 10:00" },
	{ stage: "Accounting Officer adoption", actor: "—", capacity: "Accounting Officer", outcome: "Awaiting decision", date_display: "—" },
];

function make(props = {}) {
	return mount(GovernanceHistory, { props: { history: HISTORY, ...props } });
}

describe("GovernanceHistory — U11-decisions", () => {
	it("renders every stage row in order with the exact column set", () => {
		const w = make();
		expect(w.find(".kt-card-title").text()).toBe("Decisions");
		expect(w.findAll("thead th").map((th) => th.text())).toEqual(["Stage", "Actor", "Capacity", "Decision", "Date"]);
		const rows = w.findAll("tbody tr");
		expect(rows).toHaveLength(3);
		expect(rows[0].findAll("td").map((td) => td.text())).toEqual(["Finance", "Josphat Mwangi", "Finance Confirmation Officer", "Confirmed", "4 Dec 2026, 10:00"]);
		expect(rows[1].findAll("td").map((td) => td.text())).toEqual(["Preparation", "Charles Mutiso", "Head of Procurement Function", "Signed and submitted", "7 Dec 2026, 10:00"]);
		expect(rows[2].findAll("td").map((td) => td.text())).toEqual(["Accounting Officer adoption", "—", "Accounting Officer", "Awaiting decision", "—"]);
	});

	it("never overwrites a later stage's own row when an earlier one repeats", () => {
		const w = make({
			history: [
				...HISTORY,
				{ stage: "Statutory approval", actor: "Daniel Rotich", capacity: "Responsible Cabinet Secretary", outcome: "Awaiting decision", date_display: "—" },
			],
		});
		const rows = w.findAll("tbody tr");
		expect(rows).toHaveLength(4);
		expect(rows[1].findAll("td")[3].text()).toBe("Signed and submitted"); // Preparation unaffected by a later stage
	});
});
