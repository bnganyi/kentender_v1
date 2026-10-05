// The Accounting Officer and the Head of Procurement Function after a report
// is delivered (OVS-CHG-001 v0.6 §4, §7, §15: OVS-AC-005, OVS-AC-006,
// OVS-AC-007; EVL-CHG-001 v0.5 §9.10 D07-SENT). They read the delivered
// version as an auditor does: the decision, the comparison and the report,
// read-only, with no bid to review and no action they do not hold.
//
// The payloads are the captured Report-sent world's own answers, reshaped as
// the server now sends them to these readers (viewer.oversight_full, a
// `delivered_report`, and none of the live comparison, outcome or attention).
import { describe, expect, it } from "vitest";

import { build } from "./screens/index.js";
import { isOversight, oversightRecord } from "./screens/record.js";

const FIXTURE = Object.values(import.meta.glob("./fixtures/report-sent.json", { eager: true, import: "default" }))[0];
const AUDITOR = "pw.req.auditor@example.test";
const AO = "pw.tnd.ao@example.test";

function resolved(user) {
	const answer = FIXTURE[user];
	return Object.fromEntries(Object.entries(answer).map(([part, value]) => [part, value && value.$same_as ? FIXTURE[value.$same_as][part] : value]));
}

// what the server sends an overseeing reader once a version is delivered
function overseeing(extra = {}) {
	const auditor = JSON.parse(JSON.stringify(resolved(AUDITOR).data));
	const delivered = {
		report: "EVL-1-RPT-01", version_number: 1, report_state: "Delivered", delivered: "16 Jun 2027, 14:07 EAT", recipient_name: "Charles Mutiso", review_state: "With Award",
		summary: auditor.outcome, recommendation: auditor.outcome, comparison: auditor.comparison, tender_and_committee: {}, versions: [], correction: null, ...extra,
	};
	const { comparison, outcome, attention, ...rest } = auditor;
	return { ...rest, viewer: { ...auditor.viewer, ao: true, auditor: false, bids: false, oversight_full: true, report: true, department: false },
		guidance: { ...auditor.guidance, primary_action: "view_report" }, delivered_report: delivered };
}

const context = (data, user = AO, sub = "") => ({ data, sub, id: "", user, form: {}, errors: { members: {} }, report: null, record: null });

describe("an overseeing reader after delivery", () => {
	it("is recognised only with the server's flag and a delivered report", () => {
		expect(isOversight(overseeing())).toBe(true);
		expect(isOversight({ ...overseeing(), delivered_report: undefined })).toBe(false);
		expect(isOversight({ ...overseeing(), viewer: { ...overseeing().viewer, oversight_full: false } })).toBe(false);
		expect(isOversight(resolved(AUDITOR).data)).toBe(false); // a reader of bids keeps the working record
	});

	it("reads the delivered decision and comparison on the record, not the setup-only page", () => {
		const board = build(context(overseeing()));
		expect(board.screen).toBe("results");
		const text = JSON.stringify(board);
		expect(text).toContain("Bid comparison");
		expect(text).toContain(overseeing().delivered_report.comparison.rows[0].bidder);
		expect(text).not.toContain("Report delivered"); // the old setup-only line
	});

	it("is offered View report, the committee record, and no bid to review", () => {
		const board = build(context(overseeing()));
		expect(board.pri && board.pri.label).toBe("View report");
		const labels = JSON.stringify(board);
		expect(labels).not.toContain("Review bid");
		expect(labels).toContain("Committee record");
	});

	it("sees that a returned report is being corrected, and the delivered one stays", () => {
		const correction = { returned: true, headline: "A corrected report is being prepared.", reason: "Correct the page reference.", returned_by_name: "Charles Mutiso" };
		const board = build(context({ ...overseeing({ correction, report_state: "Returned" }), state: "Reviewing" }));
		const text = JSON.stringify(board);
		expect(text).toContain("A corrected report is being prepared.");
		expect(text).toContain("returned for correction");
		expect(text).toContain("Bid comparison");
	});

	it("maps the delivered report onto the record shape without the live case", () => {
		const shaped = oversightRecord(overseeing());
		expect(shaped.attention).toEqual([]);
		expect(shaped.comparison.rows.length).toBeGreaterThan(0);
		expect(shaped.outcome.outcome).toBeTruthy();
	});

	it("an Accounting Officer before delivery still gets the setup-only page", () => {
		const before = resolved(AO).data; // the captured AO payload: no delivered_report
		expect(isOversight(before)).toBe(false);
		expect(build(context(before)).screen).toBe("setup-only");
	});
});

describe("a department head and the status-only line", () => {
	const department = (summary) => {
		const base = JSON.parse(JSON.stringify(resolved(AO).data)); // setup-only payload: no bids
		return { ...base, viewer: { ...base.viewer, ao: false, department: true }, department_summary: summary };
	};

	it("reads the outcome and the recorded reason after delivery, and nothing of the bids", () => {
		const board = build(context(department({ version_number: 1, delivered: "16 Jun 2027, 14:07 EAT", outcome: "Recommendation", recommended_bidder: "Afya Digital Supplies Limited",
			evaluated_total: "KES 46,400,000.00", reason: "The only bid received meets the published requirements.", not_an_award: "This report does not constitute an award.",
			correction: null, validity_expired: false })));
		const text = JSON.stringify(board);
		expect(board.screen).toBe("setup-only");
		expect(text).toContain("Afya Digital Supplies Limited");
		expect(text).toContain("The only bid received meets the published requirements.");
		expect(text).toContain("Report 1");
		expect(text).not.toContain("Bid comparison");
		expect(text).not.toContain("Jirani");
	});

	it("is told a correction is coming when the report was returned", () => {
		const board = build(context(department({ version_number: 1, delivered: "16 Jun 2027", outcome: "Recommendation", recommended_bidder: "Afya Digital Supplies Limited", evaluated_total: "",
			reason: "r", not_an_award: "", correction: { returned: true, headline: "A corrected report is being prepared." } })));
		expect(JSON.stringify(board)).toContain("A corrected report is being prepared.");
	});

	it("before delivery, a department head and the two offices are told why there is nothing more", () => {
		expect(JSON.stringify(build(context(department({}))))).toContain("Bid details are shared with you when the committee's report is sent.");
		const ao = resolved(AO).data; // the Accounting Officer before delivery
		expect(JSON.stringify(build(context(ao)))).toContain("Bid details are shared with you when the committee's report is sent.");
	});

	it("a reader of bids does not get that line", () => {
		const chair = resolved("pw.evl.chair@example.test").data;
		expect(JSON.stringify(build(context(chair, "pw.evl.chair@example.test")))).not.toContain("Bid details are shared with you");
	});
});

describe("a technical reader after delivery", () => {
	it("reads the delivered decision and comparison like the offices do, with no bid to review and no action", () => {
		const data = overseeing();
		const technical = { ...data, viewer: { ...data.viewer, ao: false, technical: true, oversight_full: false }, guidance: { ...data.guidance, primary_action: "" } };
		expect(isOversight(technical)).toBe(true);
		const board = build(context(technical, "Administrator"));
		expect(board.screen).toBe("results");
		const text = JSON.stringify(board);
		expect(text).toContain("Bid comparison");
		expect(text).not.toContain("Review bid");
		expect(text).not.toContain("Return for correction");
	});

	it("before delivery a technical reader keeps the status-only page", () => {
		const data = overseeing();
		const before = { ...data, delivered_report: undefined, viewer: { ...data.viewer, ao: false, technical: true, oversight_full: false } };
		expect(isOversight(before)).toBe(false);
		expect(build(context(before, "Administrator")).screen).toBe("setup-only");
	});
});

describe("the version selector for readers outside the committee", () => {
	const two = [
		{ report: "EVL-1-RPT-02", version_number: 2, state: "Delivered", delivered: "20 Jun 2027, 09:00 EAT", review_state: "With Award", outcome: "Recommendation" },
		{ report: "EVL-1-RPT-01", version_number: 1, state: "Returned", delivered: "16 Jun 2027, 14:07 EAT", review_state: "Returned", outcome: "Recommendation" },
	];
	const shown = (version) => ({ report: version.report, version_number: version.version_number, report_state: version.state, signatures: [], history: [], downstream: "",
		content: { recommendation: { outcome: "Recommendation", statement: "Award to Afya.", recommended: { bidder: "Afya Digital Supplies Limited" } }, summary: {}, financial_comparison: { rows: [] } } });
	const screen = (versions, current) => build({ ...context({ ...overseeing({ versions, report: versions[0].report, version_number: versions[0].version_number }), state: "Report sent" }, AO, "report"), id: "", report: shown(current) });
	const table = (board) => board.blocks.find((b) => b.testid === "evl-versions");

	it("lists every delivered version and links to the others, not the one shown", () => {
		const board = screen(two, two[0]);
		const t = table(board);
		expect(t).toBeTruthy();
		expect(t.rows.map((r) => r[0])).toEqual(["Report 2 (shown)", "Report 1"]);
		expect(t.rows[0][3]).toBe("");
		expect(t.rows[1][3]).toMatchObject({ label: "View", action: "nav", args: { to: ["report", "EVL-1-RPT-01"] } });
	});

	it("is absent when only one version was ever delivered", () => {
		expect(table(screen([two[0]], two[0]))).toBeUndefined();
	});

	it("a returned earlier version is still readable, and says it was returned", () => {
		const board = screen(two, two[1]);
		expect(table(board)).toBeTruthy();
		expect(JSON.stringify(board)).toContain("Report 1 was returned for correction and replaced by Report 2.");
	});

	it("the record screen offers the same list to an overseeing reader", () => {
		const board = build(context({ ...overseeing({ versions: two, version_number: 2 }), state: "Report sent" }));
		const t = board.blocks.find((b) => b.testid === "evl-versions");
		expect(t && t.rows.length).toBe(2);
	});

	it("a reader of bids does not get the selector", () => {
		const chair = resolved("pw.evl.chair@example.test").data;
		expect(table(build({ ...context(chair, "pw.evl.chair@example.test", "report"), report: shown(two[0]) }) || { blocks: [] })).toBeUndefined();
	});
});
