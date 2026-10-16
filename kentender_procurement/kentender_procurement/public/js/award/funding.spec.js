// AWD-CHG-001 v0.7 section 10.4 (AWD-FUND-AC-006): the read-only 'Funding sources' on the internal Award record, after the supported amount and before the historical detail, in its three states. The server sends
// `funding` to internal readers only; a board without it is unchanged.
import { describe, expect, it } from "vitest";

import { recordBoard } from "./screens/record.js";

const decisionRecord = {
	ok: true, award: "AWD-MOH-2027-002", tender_reference: "TND-MOH-2027-002", tender_title: "Supply and delivery of ICT equipment", procuring_entity: "Ministry of Health", stage: "Decision", cancelled: false,
	viewer: { hop: false, ao: true }, cycle: { number: 1, awaiting_report: false }, guidance: { answer: { headline: "Decide the award." }, journey: [] }, outstanding: [], history: [],
	report: { label: "Evaluation report 1", received_at: "16 Jun 2027", signatures: "5 of 5", outcome: "Award recommended", recommendation: "Recommend award to Afya Digital Supplies Limited",
		recommended: { supplier: "Afya Digital Supplies Limited", bid: "BID-1", bid_version: 1, quantity: 250, submitted: "KES 46,400,000", evaluated: "KES 46,400,000", warranty: "12 months" } },
	opinion: { signed: { label: "Professional opinion 1", signed: "Signed by Charles Mutiso", reason: "Lowest evaluated responsive bid.", conclusion: "Recommend award" } },
	notices: { preview: [] }, actions: { award_supported: true },
};
const available = {
	state: "Available", currency: "KES", unit: "Each", retained: true, total_quantity: "250", total_amount: "46400000.00", requisition: { id: "REQ-MOH-2027-004", version: "2" },
	rows: [
		{ department: "HR Management and Development", quantity: "100", amount: "18560000.00", drawdown_line: "DL-HRMD", reservation: "RSV-1", reservation_reference: "RSV-MOH-0001", budget_line: "BL-1", budget_line_title: "Hardware and IT equipment", budget_line_code: "HWD" },
		{ department: "Digital Health", quantity: "150", amount: "27840000.00", drawdown_line: "DL-DHI", reservation: "RSV-2", reservation_reference: "RSV-MOH-0002", budget_line: "BL-1", budget_line_title: "Hardware and IT equipment", budget_line_code: "HWD" },
	],
};
const titles = (b) => b.sec.map((s) => s.t);

describe("the Funding sources disclosure", () => {
	it("is a table of department, quantity and awarded amount with the total, placed after the supported amount", () => {
		const b = recordBoard({ ...decisionRecord, funding: available });
		expect(titles(b)).toEqual(["Recommendation", "Funding sources", "Professional opinion", "Decision"]);
		const s = b.sec[1];
		expect(s.tbl.h).toEqual(["Department", "Quantity", "Awarded amount"]);
		expect(s.tbl.r).toEqual([["HR Management and Development", "100 Each", "KES 18,560,000"], ["Digital Health", "150 Each", "KES 27,840,000"], ["Total", "250 Each", "KES 46,400,000"]]);
	});

	it("keeps the exact requisition, drawdown, reservation and Budget line in an expanded detail before the history", () => {
		const b = recordBoard({ ...decisionRecord, funding: available });
		const names = b.disc.map((x) => x.t || x);
		expect(names.indexOf("Funding source details")).toBeGreaterThan(-1);
		const lines = b.disc.find((x) => x.t === "Funding source details").lines;
		expect(lines).toHaveLength(2);
		expect(lines[0]).toContain("Requisition REQ-MOH-2027-004, version 2");
		expect(lines[0]).toContain("Reservation RSV-MOH-0001");
		expect(lines[0]).toContain("Budget line Hardware and IT equipment (HWD)");
	});

	it("says the awarded items could not be matched when the sources are missing, never an empty table", () => {
		const message = "The awarded items could not be matched to their funding sources. Procurement must resolve the source details.";
		const b = recordBoard({ ...decisionRecord, funding: { state: "Missing", message } });
		const s = b.sec.find((x) => x.t === "Funding sources");
		expect(s.p).toEqual([`!${message}`]);
		expect(s.tbl).toBeUndefined();
		expect(b.disc.map((x) => x.t || x)).not.toContain("Funding source details");
	});

	it("says funding details are unavailable when an owner cannot answer", () => {
		const b = recordBoard({ ...decisionRecord, funding: { state: "Unavailable", message: "Funding details are unavailable. The system will retry." } });
		expect(b.sec.find((x) => x.t === "Funding sources").p).toEqual(["!Funding details are unavailable. The system will retry."]);
	});

	it("is absent when the server sent none (a supplier, a technical reader, a closed award)", () => {
		expect(titles(recordBoard(decisionRecord))).toEqual(["Recommendation", "Professional opinion", "Decision"]);
		expect(titles(recordBoard({ ...decisionRecord, funding: null }))).not.toContain("Funding sources");
	});
});
