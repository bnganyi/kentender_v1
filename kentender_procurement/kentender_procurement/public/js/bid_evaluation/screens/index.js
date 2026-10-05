// Which board a route shows (EVL-CHG-001 v0.4 §10). The route names the
// place; the server's state and this viewer's place in it decide what that
// place shows. Sub-routes under /app/tenders/{ref}/evaluation:
//   ""                     the record: results, or the live discussion
//   record                 the committee record (tab)
//   appoint | secretary | replace | declaration | unable   committee setup
//   bid/{bid}              one opened bid's requirements
//   discussion             the live committee discussion
//   clarification/{id}     one clarification request
//   report | report/preview | report/{version}   the evaluation report
//   verification           the due-diligence exercise
//   update/{event}         an opening-record update
//   correction             a correction notice (chair) or its review (Head)
//   issue                  the recorded support issue
import * as committee from "./committee.js";
import * as record from "./record.js";
import { bidScreen, concernDialog as bidConcern, issueDialog } from "./bid.js";
import { discussion, disagreeDialog } from "./discussion.js";
import { clarification, withdrawDialog } from "./clarification.js";
import { concernDialog as reportConcern, preview, reportScreen, returnDialog, reviseDialog, statusIssueDialog } from "./report.js";
import { correction, issue, update, verification } from "./followups.js";
import { committeeRecord } from "./committee_record.js";

// What a route needs loaded beside the evaluation itself.
export function needs(sub, id, data) {
	const out = {};
	if (sub === "bid" && id) out.bid = id;
	if (["report", "correction"].includes(sub) || (data && data.state === "Report sent" && sub === "update")) out.report = sub === "report" && id && id !== "preview" ? id : "";
	if (["record", "replace"].includes(sub) || (data && data.state === "No evaluation required")) out.record = true;
	// the main route shows the appointment or secretary form when that is the
	// viewer's next step (pick()), so it needs the same pick list
	const primary = ((data && data.guidance) || {}).primary_action || "";
	if (sub === "appoint" || sub === "replace" || (sub === "" && primary === "appoint_committee")) out.candidates = "committee";
	if (sub === "secretary" || (sub === "" && primary === "assign_secretary")) out.candidates = "secretary";
	if (data && (data.work || {}).session && ["", "discussion"].includes(sub)) {
		const item = (data.attention || [])[0] || ((data.work || {}).clarifications || []).find((c) => c.status === "Sent" && (c.reply || c.overdue));
		if (item) out.bid = item.evaluation_bid;
		else if (((data.comparison || {}).rows || [])[0]) out.bid = data.comparison.rows[0].bid;
	}
	if (sub === "verification" && ((data && data.comparison) || {}).rows && data.comparison.rows[0]) out.bid = data.comparison.rows[0].bid;
	return out;
}

// The board for this route, named for the page-ready hook (`data-screen`).
export function build(ctx) {
	const [screen, board] = pick(ctx);
	return board ? { ...board, screen } : null;
}

function pick(ctx) {
	const { data, sub } = ctx;
	const v = data.viewer || {};
	const primary = (data.guidance || {}).primary_action || "";
	const nf = record.states("not-found");
	// a technical reader acts in no business capacity: status only, and once a version is delivered the delivered
	// record, report and committee record read-only (OVS-CHG-001 v0.6 §4.2)
	if (v.technical && !(record.isOversight(data) && ["", "report", "record"].includes(sub))) return ["setup-only", record.setupOnly(ctx)];
	switch (sub) {
		case "appoint": return ["appoint", committee.appoint(ctx)];
		case "secretary": return ["secretary", committee.secretary(ctx)];
		case "declaration": return ["declaration", committee.declaration(ctx)];
		case "replace": return ["replace", committee.replace(ctx)];
		case "unable": return ["unable", committee.unable(ctx)];
		case "record": return ["committee-record", committeeRecord(ctx)];
		case "bid": return ["bid", bidScreen(ctx)];
		case "clarification": return ["clarification", clarification(ctx) || nf];
		case "report": return ctx.id === "preview" ? ["report-preview", preview(ctx) || nf] : ["report", reportScreen(ctx) || nf];
		case "verification": return ["verification", verification(ctx) || nf];
		case "update": return ["update", update(ctx) || nf];
		case "correction": return ["correction", correction(ctx) || nf];
		case "issue": return ["issue", issue(ctx)];
		default: break;
	}
	if (data.state === "No evaluation required") return ["no-bids", record.noBids(ctx)];
	if (data.state === "Cancelled") return ["cancelled", record.cancelled(ctx)];
	if ((data.conditions || {}).suspended) return ["paused", record.paused(ctx)];
	if (primary === "appoint_committee") return ["appoint", committee.appoint(ctx)];
	if (primary === "assign_secretary") return ["secretary", committee.secretary(ctx)];
	if (v.undeclared) return ["declare-first", committee.declareFirst(ctx)];
	if (data.state === "Preparing") return ["preparing", record.preparing(ctx)];
	if (record.isOversight(data)) return ["results", record.results({ ...ctx, data: record.oversightRecord(data) })];
	if (!v.bids) return ["setup-only", record.setupOnly(ctx)];
	if ((data.work || {}).session && (v.member || v.secretary)) {
		const live = discussion(ctx);
		if (live) return ["discussion", live];
	}
	return ["results", record.results(ctx)];
}

export function dialogFor(name, ctx) {
	switch (name) {
		case "concern": return ctx.sub === "bid" ? bidConcern(ctx) : reportConcern(ctx);
		case "issue": return issueDialog(ctx);
		case "disagree": return disagreeDialog(ctx);
		case "withdraw": return withdrawDialog(ctx);
		case "revise": return reviseDialog(ctx);
		case "return": return returnDialog(ctx);
		case "status-issue": return statusIssueDialog(ctx);
		case "instruction": return record.instructionDialog(ctx.data);
		default: return null;
	}
}

export { record };
