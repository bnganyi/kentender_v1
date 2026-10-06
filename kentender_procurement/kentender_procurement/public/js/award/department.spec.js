// A Head of User Department whose unit contributed reads the Award as a department-level view
// (OVS-CHG-001 v0.6 P03; owner decision 4 Oct 2026): the stage, who it is with, and once recorded the
// outcome, date and reason. Nothing else is on the board.
import { describe, expect, it } from "vitest";

import { departmentBoard, recordBoard } from "./screens/record.js";

const base = { ok: true, department: true, award: "AWD-MOH-2027-002", tender_reference: "TND-MOH-2027-002", tender_title: "Supply and delivery of ICT equipment", stage: "Opinion",
	cancelled: false, decision: null, outstanding: "Charles Mutiso is preparing the professional opinion.", notification_status: "" };
const text = (b) => JSON.stringify(b);

describe("the department view of the Award", () => {
	it("before a decision it names the stage and who it is with, and says when details follow", () => {
		const b = recordBoard(base);
		expect(b.screen).toBe("department");
		expect(b.sec[0].t).toBe("Award stage");
		expect(b.sec[0].f).toEqual([["Stage", "Opinion"]]);
		expect(b.sec[0].p).toEqual(["Charles Mutiso is preparing the professional opinion.", "Details are shared with you when the Accounting Officer records the decision."]);
		expect(b.act).toEqual([]);
	});

	it("after the decision it shows the outcome, date, who decided, notices and the reason", () => {
		const b = departmentBoard({ ...base, stage: "Notices", decision: { outcome: "Award", by: "Amina Hassan", at: "20 Jun 2027, 10:00 EAT", reason: "Lowest evaluated responsive bid." }, outstanding: "", notification_status: "Notices given" });
		expect(b.sec[0].t).toBe("Decision");
		expect(b.sec[0].f).toEqual([["Outcome", "Award"], ["Decision recorded", "20 Jun 2027, 10:00 EAT"], ["Decided by", "Amina Hassan"], ["Notices", "Notices given"]]);
		expect(b.sec[0].d).toEqual([["Reason", "Lowest evaluated responsive bid."]]);
		expect(b.sec[0].p).toEqual([]);
	});

	it("a cancelled tender says so", () => {
		expect(departmentBoard({ ...base, cancelled: true, outstanding: "" }).sec[0].p[0]).toBe("This tender was cancelled. Award ended.");
	});

	it("carries no action and no opinion, report or bidder wording", () => {
		const t = text(recordBoard(base));
		for (const word of ["Sign opinion", "Award and notify", "Return for correction", "Evaluation report", "Bid comparison", "Professional opinion"]) expect(t).not.toContain(word);
	});
});
