// The evaluation report (EVL-CHG-001 v0.4 §9.8, §9.11, §9.12, §9.13; boards
// D07-DRAFT, D07-SIGN, D07-WAIT, D07-CONCERN, D07-SENT, D07-HOP,
// D07-HOP-RETURN, D07-RETURNED, D07-NO-RESPONSIVE, D07-NO-AGREEMENT,
// D07-REVISE(-DLG), D07-DELIVERY, D07-OVERDUE(-SEC), D07-EXPIRED(-SIGN,-SENT),
// D07-INCOMPLETE, D07-DECISION-UNKNOWN(-CHAIR), D07-TIE, D07-FUNDING,
// D07-PREVIEW, S-STALE-REPORT, S-UNCONFIRMED, S-AUDITOR).
//
// Generated from the record: only the committee summary is editable, and
// only by the secretary while Reviewing. Signing is personal and exact to
// one frozen version; the last proof delivers with no further click.
import { at, ds, f, fi, kv, lk, n, p, tb } from "../board/model.js";
import { cmd, conditionNotices, dialog, guidance, money, nav, sectionLinks, signaturesTable, summaryBlock } from "./common.js";

const INTENT = "I have reviewed this report. It accurately records my findings and any disagreement I have recorded.";

function outcomeBlocks(report) {
	const c = report.content || {};
	const rec = c.recommendation || {};
	const fin = c.financial_comparison || { rows: [] };
	if (rec.outcome === "No single recommendation — equal evaluated totals") {
		return [kv([["Outcome", rec.outcome], ["Reason", rec.reason]], { title: "Summary" }),
			tb(["Bidder", "Submitted total", "Adjustments", "Evaluated total", "Position"], fin.rows.map((r) => [r.bidder, money(r.currency, r.submitted_total), r.adjustments,
				money(r.currency, r.evaluated_total), String(r.position)]), { title: "Financial comparison", sec: true })];
	}
	if (rec.outcome === "No responsive bids") {
		const f0 = (c.bid_findings || [])[0] || { groups: {} };
		return [kv([["Recommendation", rec.outcome], ["Reason", rec.reason], ["Eligibility", f0.groups["EVG-ELIGIBILITY"] || ""], ["Technical compliance", f0.groups["EVG-TECHNICAL-COMPLIANCE"] || ""]], { title: "Summary" }),
			tb(["Submitted total", "Evaluation adjustments", "Evaluated total", "Position"], fin.rows.map((r) => [money(r.currency, r.submitted_total), r.adjustments, r.evaluated_total, String(r.position)]),
				{ title: "Financial comparison", sec: true, caption: "The submitted total is a source fact, not a recommended amount." })];
	}
	if (rec.outcome === "No agreed recommendation") {
		const said = ((c.clarifications_and_record || {}).disagreements || []);
		return [kv([["Recommendation", rec.outcome]], { title: "Summary" }),
			tb(["Member", "Recorded position"], said.map((d) => [d.member, d.statement]), { title: "Attributed positions", sec: true, caption: "These positions remain unresolved. No majority decision is inferred." })];
	}
	if (rec.outcome === "No current recommendation — tender validity expired") {
		return [kv([["Outcome", `${rec.outcome}.`]], { title: "Summary" })];
	}
	return [summaryBlock(c)];
}

function history(report) {
	const rows = (report.history || []).filter((h) => h.name !== report.report);
	return ds("Report history", rows.length ? rows.map((h) => `Report ${h.version_number} · ${h.state}${h.supersession_reason ? ` — ${h.supersession_reason}` : ""}`) : "No earlier report.", { open: rows.some((h) => h.state === "Returned") });
}

export function reportScreen(ctx) {
	const { data, report, user, form } = ctx;
	if (!report) return null;
	const v = data.viewer;
	const work = data.work || {};
	const n0 = report.version_number;
	const draftDesc = `${data.tender} · Draft report ${n0}`;
	const crumbHead = { title: "Evaluation report", desc: draftDesc };
	const noticeBlocks = conditionNotices(data).filter((b) => !(report.content && (report.content.recommendation || {}).outcome === "No current recommendation — tender validity expired" && b.k === "facts"));

	// Report sent (D07-SENT, D07-HOP, D07-DECISION-UNKNOWN, S-AUDITOR)
	if (report.report_state === "Delivered" || report.report_state === "Returned" && data.state === "Report sent") {
		const sent = [...outcomeBlocks(report), sectionLinks(), signaturesTable(report.signatures, user, data), f(["Current report", `Report ${n0}`])];
		const delivery = work.delivery || {};
		const base = { title: `Evaluation report ${n0}`, desc: data.tender, guidance: guidance(data) };
		if (v.hop && delivery.recipient_user === user) {
			if (report.downstream === "Unknown") {
				return { ...base, guidance: guidance(data, { headline: "Report the unavailable decision status." }),
					blocks: [n("warning", "The later decision could not be checked.", `Report ${n0} remains unchanged. A return cannot proceed until the later decision is known.`), ...sent.slice(0, -2)],
					sec: [{ label: "Open report", action: "nav", args: { to: ["report", "preview"] } }, { label: "~Return for correction" }] };
			}
			return { ...base, blocks: sent.slice(0, -1), pri: nav("Open report", ["report", "preview"]),
				sec: report.downstream === "Award decision recorded" ? [] : [dialog("Return for correction", "return")] };
		}
		if (v.chair && report.downstream === "Award decision recorded") {
			return { ...base, blocks: sent, pri: nav("Send correction notice", "correction"), sec: [nav("Open report", ["report", "preview"])] };
		}
		return { ...base, blocks: [...noticeBlocks.filter((b) => b.k === "notice"), ...sent], sec: [{ label: "Download report", action: "download" }, nav("View committee record", "record")] };
	}

	// Signing (D07-SIGN, D07-WAIT, D07-REVISE, D07-DELIVERY, D07-EXPIRED-SIGN, S-STALE-REPORT, S-UNCONFIRMED)
	if (report.report_state === "Signing" || report.report_state === "Superseded") {
		const current = (work.signing || {}).report;
		const blocks = [...noticeBlocks.filter((b) => b.k === "notice"), ...outcomeBlocks(report), sectionLinks(), signaturesTable(report.signatures, user, data)];
		const base = { title: `Evaluation report ${n0}`, desc: data.tender, guidance: guidance(data) };
		const download = { label: "Download report", action: "download" };
		if (current && report.report !== current) {
			return { ...base, guidance: guidance(data, { headline: "The report changed. Review the latest version before signing." }), blocks,
				pri: nav("Review latest report", "report"), sec: [download] };
		}
		const mine = (report.signatures || []).find((s) => s.member === user);
		if (ctx.unconfirmed && mine && !mine.signed) {
			return { ...base, guidance: guidance(data, { headline: "Your signature has not been confirmed." }), blocks,
				pri: cmd("Check signature status", "sign_report", { values: { report_version: report.report }, reuseKey: "sign" }), sec: [download] };
		}
		const delivery = work.delivery || {};
		if (v.secretary && delivery.status === "Failed" && delivery.report_version === report.report) {
			return { ...base, blocks, pri: cmd("Retry delivery", "retry_delivery"), sec: [download] };
		}
		if (v.secretary || (v.chair && !(mine && !mine.signed) && form.revise)) {
			return { ...base, guidance: guidance(data, v.secretary ? { headline: "Correct the report before collecting further signatures." } : {}), blocks, pri: dialog("Revise report", "revise"), sec: [] };
		}
		if (mine && !mine.signed) {
			return { ...base, blocks: [...blocks, p(INTENT)], pri: cmd("Sign report", "sign_report", { values: { report_version: report.report }, reuseKey: "sign" }),
				sec: [dialog("Raise a concern", "concern"), download] };
		}
		return { ...base, blocks, sec: v.eligible ? [dialog("Raise a concern", "concern"), download] : [download] };
	}

	// Reviewing: the live draft (D07-DRAFT, D07-RETURNED, D07-INCOMPLETE, D07-OVERDUE, D07-EXPIRED, outcomes)
	const blocks = [...noticeBlocks];
	const returned = work.delivery && work.delivery.review_state === "Returned" ? work.delivery : null;
	if (returned && v.secretary) blocks.push(at(returned.return_comment, `Returned by ${returned.returned_by_name || ""}`.trim()));
	const issues = report.readiness || [];
	if (v.secretary && issues.length) {
		blocks.push(n("warning", "Review the listed issues before sending the report for signing."),
			tb(["Open issue", "Holder"], issues.map((i) => [i.label || i.message || "", i.holder_name || ""]), { title: "Unresolved", sec: true, testid: "evl-unresolved" }), sectionLinks());
		const first = issues.find((i) => i.bid) || {};
		return { ...crumbHead, guidance: guidance(data), blocks,
			pri: first.bid ? nav("Open issue", ["bid", first.bid]) : null,
			sec: [{ label: "~Send for signing" }, cmd("Save draft", "save_report_narrative", { fields: ["narrative"], reportVersion: true }), nav("Preview report", ["report", "preview"])] };
	}
	blocks.push(...outcomeBlocks(report), sectionLinks());
	if (v.secretary) {
		blocks.push(fi("Committee summary", "", { area: true, rows: 3, name: "narrative" }), history(report));
		return { ...crumbHead, guidance: guidance(data), blocks,
			pri: cmd("Send for signing", "send_report_for_signing", { reportVersion: true, saveNarrative: true }),
			sec: [cmd("Save draft", "save_report_narrative", { fields: ["narrative"], reportVersion: true }), nav("Preview report", ["report", "preview"])],
			cons: "Each member will review and sign this exact report. Changes will require a new version." };
	}
	return { ...crumbHead, guidance: guidance(data), blocks, pri: nav("Preview report", ["report", "preview"]), sec: [nav("Back to evaluation", [])] };
}

export function preview(ctx) {
	const { data, report, user } = ctx;
	if (!report) return null;
	const c = report.content || {};
	const tc = c.tender_and_committee || {};
	const blocks = [
		kv([["Tender", `${tc.tender} · ${tc.title}`], ["Opening", tc.opening_completed ? `Completed ${tc.opening_completed}` : ""], ["Bids opened", String(tc.bids_opened || 0)],
			["Appointment", tc.appointment_reference || ""]], { title: "Tender and committee", anchor: "Tender and committee" }),
		tb(["Person", "Department", "Capacity"], (tc.members || []).map((m) => [m.name, m.department, m.capacity]).concat(tc.secretary ? [[tc.secretary.name, "Procurement", "Secretary — not a voting or signing member"]] : [])),
	];
	(c.bid_findings || []).forEach((b) => {
		blocks.push(tb(["Requirement", "Offered or recorded evidence", "Finding"], b.eligibility.map((r) => [r.requirement, r.evidence || r.reason, r.finding]), { title: `Bid findings — Eligibility · ${b.bidder}`, anchor: "Bid findings",
			caption: "Responsive means the bid meets the applicable mandatory requirements." }));
		blocks.push(tb(["Requirement", "Offered or recorded evidence", "Finding"], b.technical.map((r) => [r.requirement, r.evidence || r.reason, r.finding]), { title: `Bid findings — Technical compliance · ${b.bidder}`, sec: true }));
	});
	const fin = c.financial_comparison || { rows: [], prices: [] };
	blocks.push(tb(["Bidder", "Submitted total", "Adjustments", "Evaluated total", "Position"], fin.rows.map((r) => [r.bidder, money(r.currency, r.submitted_total), r.adjustments,
		/^[0-9.]+$/.test(String(r.evaluated_total || "")) ? money(r.currency, r.evaluated_total) : r.evaluated_total, String(r.position)]), { title: "Financial comparison", anchor: "Financial comparison" }));
	const rec = c.clarifications_and_record || {};
	const rows = [];
	(rec.clarifications || []).forEach((q) => {
		rows.push(["Question", q.question], ["Sent", q.sent], ["Deadline", q.deadline]);
		if (q.reply) rows.push(["Reply", `Received ${q.reply.received}${q.reply.timeliness === "Late" ? " (late)" : ""}`]);
		if (q.status === "Closed") rows.push(["Committee outcome", `${q.closed} — ${q.disposition_reason}`]);
	});
	(rec.sessions || []).forEach((s) => rows.push(["Session", `${s.start}–${(s.end || "").split(", ")[1] || ""}, ${s.subject}. ${s.attendance.map((a) => `${a.name} ${(a.joined || "").split(", ")[1] || ""}`).join(", ")}`]));
	rows.push(["Disagreement", (rec.disagreements || []).length ? rec.disagreements.map((d) => `${d.member}: ${d.statement}`).join(" ") : "No disagreement recorded"]);
	rows.push(["Due diligence", (c.summary || {}).diligence || ""]);
	blocks.push(kv(rows, { title: "Clarifications and committee record", anchor: "Clarifications and committee record" }));
	blocks.push(p((c.recommendation || {}).statement || "", { strong: true, title: "Recommendation and reasons", anchor: "Recommendation and reasons" }));
	blocks.push(signaturesTable(report.live ? (tc.members || []).map((m) => ({ member: m.user, name: m.name, signed: "" })) : report.signatures, "", data, {}));
	if (report.live) blocks[blocks.length - 1].rows = blocks[blocks.length - 1].rows.map((r) => [r[0], r[1], "Not yet signed"]);
	return { title: "Evaluation report", desc: `${data.tender} · ${report.live ? "Draft" : ""} report ${report.version_number}`.replace("  ", " "), blocks,
		guidance: { answer: null, journey: data.tracker },
		sec: [nav("Back to report", "report")], printable: true };
}

export function concernDialog() {
	return {
		t: "Raise a concern",
		blocks: [fi("What needs correction?", "", { area: true, req: true, rows: 3, name: "concern_reason" })],
		cons: "The report will return for correction. All members will need to sign the new version.",
		pri: cmd("Send concern", "raise_report_concern", { fields: [["reason", "concern_reason"]], close: true }),
	};
}

export function reviseDialog() {
	return {
		t: "Revise report",
		blocks: [fi("Reason", "", { area: true, req: true, rows: 2, name: "revise_reason" })],
		cons: "A new report will need all members' signatures.",
		pri: cmd("Revise report", "revise_report", { fields: [["reason", "revise_reason"]], close: true }),
	};
}

export function returnDialog(ctx) {
	const { report } = ctx;
	return {
		t: "Return for correction",
		blocks: [kv([["Downstream status", `${report.downstream || "No award decision recorded"}${report.downstream_checked ? ` · checked ${report.downstream_checked}` : ""}`]]),
			fi("Reason", "", { area: true, req: true, rows: 2, name: "return_comment" })],
		pri: cmd("Return report", "return_report", { fields: [["comment", "return_comment"]], close: true }),
	};
}

export { lk };
