// The evaluation record (EVL-CHG-001 v0.4 §9.4, §9.10, §9.11, §9.13; boards
// D03, D03-READY, D03-FUNDING, D03-TIE, D02-NO-BIDS, S-CHECKS,
// S-OPENING-AWAITED, S-SOURCE-OPEN, D08-SOURCE, D08-PAUSED, D08-CANCELLED,
// P-PREP, P-SIGN, C-PREP, C-SIGN, S-AUDITOR). What the record shows follows
// the server's state and this viewer's place in it; the primary action is
// the server's guidance, never inferred here.
import { at, ds, em, f, kv, n, tb } from "../board/model.js";
import { cmd, comparisonTable, conditionNotices, dialog, guidance, head, money, nav, ownerEvent, recordTabs, rosterTable, signaturesTable, sourceDisclosure, versionsBlock } from "./common.js";

// The primary action the server's guidance names, as the button that does it
// here (a command) or opens the screen where it is done (a navigation).
export function primaryFor(data, ctx) {
	const action = (data.guidance || {}).primary_action || "";
	const work = data.work || {};
	const clar = (work.clarifications || []).find((c) => c.status === "Authorised" || (c.status === "Sent" && c.notice_state === "Delivery problem"));
	const firstBid = ((data.comparison || {}).rows || [])[0];
	switch (action) {
		case "appoint_committee": return nav("Appoint committee", "appoint");
		case "assign_secretary": return nav("Assign secretary", "secretary");
		case "complete_declaration": return nav("Complete declaration", "declaration");
		case "replace_member": return nav("Replace member", "replace");
		case "start_discussion": return cmd("Start discussion", "start_discussion", { values: { subject: subjectFor(data) } });
		case "join_discussion": return cmd("Join discussion", "join_discussion");
		case "review_bid": return firstBid ? nav("Review bid", ["bid", firstBid.bid]) : null;
		case "send_clarification": return clar ? nav("View clarification", ["clarification", clar.name]) : null;
		case "retry_notice": return clar ? nav("View clarification", ["clarification", clar.name]) : null;
		case "record_observation": case "send_verification": case "sign_verification": return nav("View verification", "verification");
		case "record_impact": {
			const update = (work.updates || []).find((u) => !u.impact || u.impact === "Pending");
			return update ? nav("Review opening update", ["update", update.name]) : null;
		}
		case "open_issue": case "send_for_signing": case "sign_report": case "retry_delivery": case "view_report": case "open_report":
			return nav("View report", "report");
		case "open_new_evidence": return nav("Open new evidence", "correction");
		default: return null;
	}
}

function subjectFor(data) {
	const item = (data.attention || [])[0];
	return item ? item.subject : "Committee discussion";
}

function attentionBlocks(data) {
	return (data.attention || []).map((item) => at(item.subject, `${item.opened_by_name}, ${item.opened} · Task: Resolve evaluation concern for ${data.tender}`));
}

function outcomeBlocks(data) {
	const o = data.outcome || {};
	const rows = (data.comparison || {}).rows || [];
	const out = [];
	if (o.outcome === "Recommendation" && o.recommended) {
		if (rows.length === 1) out.push(at(`${o.recommended.bidder} is the only responsive bidder.`));
		const funds = o.funding;
		if (funds && funds.qualification) out.push(f(["Available funding", money("KES", funds.available)], ["Shortfall", money("KES", funds.shortfall)], ["Source", funds.source || "Budget confirmation"]));
		out.push(at(`Recommendation: ${o.recommended.bidder} · ${money(o.recommended.currency, o.recommended.evaluated_total)}.`, funds && funds.qualification ? funds.qualification : "", { strong: true }));
	} else if (o.outcome) {
		out.push(at(`${o.outcome}.`, o.reason || "", { strong: true }));
	}
	return out;
}

// The Accounting Officer and the Head of Procurement Function, once a report
// version is delivered, read it as an auditor does (EVL-CHG-001 v0.5 §9.10,
// D07-SENT; OVS-CHG-001 v0.6 §4): read-only, from the delivered version the
// server froze, never the live case. The server sends that version as
// `delivered_report`; the record screen below is built from it unchanged.
export function oversightRecord(data) {
	const d = data.delivered_report || {};
	return { ...data, comparison: { label: "", ...(d.comparison || {}) }, outcome: d.recommendation || {}, attention: [] };
}

// the two offices and a technical reader, once a version is delivered; a reader of bids keeps the working record
export const isOversight = (data) => !!(data.viewer && (data.viewer.oversight_full || data.viewer.technical) && !data.viewer.bids && data.delivered_report);

// D03 family: the record as a reader of bids sees it.
export function results(ctx) {
	const { data } = ctx;
	const oversight = isOversight(data);
	const table = data.comparison || { rows: [] };
	const blocks = [...conditionNotices(data)];
	const caption = table.label === "Provisional comparison" ? "Provisional comparison." : (data.attention || []).length ? "The offered values have been checked. One supporting-evidence question remains." : "";
	const returned = oversight ? (data.delivered_report || {}).correction : null;
	if (returned) {
		blocks.unshift(n("info", `Report ${data.delivered_report.version_number} was returned for correction.`, `${returned.headline} ${returned.reason || ""}`.trim()));
	}
	// an overseeing reader has no bid to review: the comparison carries no action
	blocks.push(comparisonTable(data, { ...(caption ? { caption } : {}), ...(oversight ? { noAction: true } : {}) }));
	blocks.push(...attentionBlocks(data), ...outcomeBlocks(data));
	const versions = oversight ? versionsBlock(data, (data.delivered_report || {}).report) : null;
	if (versions) blocks.push(versions);
	const source = sourceDisclosure(data);
	if (source) blocks.push(source);
	const pri = primaryFor(data, ctx);
	const sec = [];
	if (!pri || pri.label !== "View report") sec.push(nav("View report", "report"));
	if (ctx.tab !== 1) sec.push(nav("Committee record", "record"));
	return { ...head(data), ...recordTabs(0), guidance: guidance(data), blocks, pri, sec: pri ? sec : sec };
}

// S-OPENING-AWAITED, S-CHECKS, S-SOURCE-OPEN / D08-SOURCE: Preparing states.
export function preparing(ctx) {
	const { data } = ctx;
	const issue = ((data.work || {}).issues || []).find((i) => i.status === "Open" && i.operation === "ReceiveOpeningPackage");
	if (issue) {
		return {
			...head(data), guidance: guidance(data),
			blocks: [n("warning", "Some opened bid information could not be loaded."), f(["Source", data.source ? `Opening completed ${data.source.opening_completed}` : "Opening completed"]),
				kv([["Recorded", `System, ${issue.opened}`], ["Assigned to", `${(issue.holders || []).join(", ") || "Technical support"}, Technical support`], ["Reason", issue.safe_detail || issue.subject]], { title: "Support issue", sec: true })],
			pri: nav("View issue", "issue"), sec: data.viewer.secretary ? [cmd("Try again", "retry_intake")] : [],
		};
	}
	if (data.source) {
		return { ...head(data), guidance: guidance(data), notInvolved: "Automatic checks are running.", blocks: [sourceDisclosure(data)].filter(Boolean) };
	}
	const blocks = (data.committee || {}).members && data.committee.members.length ? [rosterTable(data)] : [f(["Tender", data.tender], ["Title", data.title])];
	return { ...head(data), guidance: guidance(data), blocks, pri: primaryFor(data, ctx) };
}

// D02-NO-BIDS: an empty opening; nothing to evaluate.
export function noBids(ctx) {
	const { data } = ctx;
	const rec = ctx.record || {};
	const rows = [];
	(rec.appointments || []).forEach((a) => rows.push([`Committee ${a.kind === "Initial" ? "appointed" : a.kind.toLowerCase()} · ${a.reference}`, "", a.at]));
	const sec = (data.committee || {}).secretary;
	if (sec) rows.push([`Secretary assigned · ${sec.reference}`, "", ""]);
	(rec.declarations || []).forEach((d) => rows.push([`Declaration · ${d.choice === "Declare a conflict" ? "conflict declared" : "no conflict"}`, d.member, d.at]));
	return {
		...head(data), guidance: guidance(data),
		blocks: [tb(["Event", "Person", "Recorded"], rows, { title: "Appointment and declaration history", sec: true }), { k: "links", links: [{ label: "View opening record", action: "nav-opening" }], title: "Source", sec: true }],
		sec: [nav("Back to evaluations", "workspace")],
	};
}

// D08-PAUSED / P-PREP / P-SIGN: a recorded suspension.
export function paused(ctx) {
	const { data } = ctx;
	const e = ownerEvent(data, "Suspension") || {};
	const facts = f(["Instruction", e.instruction_reference || ""], ["Received", e.received || ""], ["Transmitted by", e.authority_name ? `${e.authority_name}, Accounting Officer` : ""]);
	const blocks = [];
	if (data.state === "Preparing") {
		blocks.push(n("warning", "Evaluation is paused by the recorded instruction."), facts);
		return { ...head(data), guidance: guidance(data), blocks, pri: primaryFor(data, ctx), sec: [dialog("View instruction", "instruction")] };
	}
	blocks.push(facts);
	if (data.state === "Signing" && (data.work || {}).signing) blocks.push(signaturesTable(data.work.signing.signatures, ctx.user, data));
	else if (data.comparison) blocks.push(comparisonTable(data, { title: "Current findings (read-only)", sec: true, noAction: true }));
	return { ...head(data), guidance: guidance(data), blocks, sec: [dialog("View instruction", "instruction"), nav("View report", "report")] };
}

// D08-CANCELLED / C-PREP / C-SIGN: the evaluation ended.
export function cancelled(ctx) {
	const { data } = ctx;
	const e = ownerEvent(data, "Cancellation") || {};
	const blocks = [];
	if (data.comparison && data.comparison.rows.length && !(data.work || {}).signing) {
		blocks.push(f(["Authority", e.authority_name || ""], ["Source", "Tenders"], ["Reason", e.reason || ""]),
			comparisonTable(data, { title: "Partial findings", sec: true, noAction: true, caption: "Evaluation ended before a report was sent." }));
	} else {
		blocks.push(f(["Instruction", e.instruction_reference || ""], ["Received", e.received || ""], ["Authority", e.authority_name ? `${e.authority_name}, Accounting Officer` : ""]));
		if ((data.work || {}).signing) blocks.push(signaturesTable(data.work.signing.signatures, ctx.user, data));
	}
	const sec = [dialog("View cancellation notice", "instruction")];
	if (data.committee && (data.committee.members || []).length) sec.push(nav("View committee record", "record"));
	return { ...head(data), guidance: { answer: { ...(data.guidance || {}), sentence: e.received ? `Cancelled on ${e.received}.` : "" }, journey: data.tracker }, blocks, sec };
}

// What a reader outside the committee is told about the bids (OVS-CHG-001 v0.6
// §4, §4.1; owner decision 4 Oct 2026, "a department-level view"). Before a report is
// delivered, a plain line says why there is nothing more. A Head of User
// Department whose unit contributed then reads the outcome, the recommendation
// and its recorded reason, never the bids, the findings or the report.
export function departmentBlocks(data) {
	const v = data.viewer || {};
	const s = data.department_summary;
	if (v.department && s && s.outcome) {
		const out = [f([s.recommended_bidder ? "Recommendation" : "Outcome", s.recommended_bidder || s.outcome], ["Evaluated total", s.evaluated_total || ""],
			["Report", `Report ${s.version_number}`], ["Report sent", s.delivered || ""])];
		if (s.reason) out.push(at(s.reason, "Recorded reason"));
		if (s.not_an_award) out.push(n("info", s.not_an_award));
		if (s.correction) out.push(n("info", `Report ${s.version_number} was returned for correction.`, s.correction.headline));
		return out;
	}
	if ((v.department || v.ao || v.hop) && !data.delivered_report) return [n("info", "Bid details are shared with you when the committee's report is sent.")];
	return [];
}

// A reader with no bid access (Accounting Officer, Head of Procurement before
// delivery, a technical reader): setup and status only.
export function setupOnly(ctx) {
	const { data } = ctx;
	const blocks = [];
	if (data.viewer.technical) blocks.push(f(["Tender", data.tender], ["State", data.state]));
	else blocks.push(rosterTable(data));
	const delivery = (data.work || {}).delivery;
	if (delivery && delivery.status === "Delivered") blocks.push(f(["Report", `Report ${delivery.report_version ? "" : ""}delivered`.trim()], ["Delivered", delivery.delivered]));
	blocks.push(...departmentBlocks(data));
	return { ...head(data), guidance: guidance(data), blocks, pri: data.viewer.technical ? null : primaryFor(data, ctx), sec: [nav("Back to evaluations", "workspace")] };
}

export function instructionDialog(data) {
	const e = ownerEvent(data, "Cancellation") || ownerEvent(data, "Suspension") || {};
	return {
		t: e.kind === "Cancellation" ? "Cancellation notice" : "Recorded instruction",
		blocks: [kv([["Instruction", e.instruction_reference || ""], ["Received", e.received || ""], ["Authority", e.authority_name || ""], ["Reason", e.reason || "—"]])],
		pri: { label: "Close", action: "close-dialog" }, sec: [],
	};
}

export function states(kind) {
	if (kind === "loading") return { blocks: [em("Loading evaluation…", null, "loader")] };
	if (kind === "not-found") return { blocks: [em("This evaluation is not available.", null, "search")], sec: [nav("Back to evaluations", "workspace")] };
	return { blocks: [em("We could not load this evaluation.", null, "alert")], pri: { label: "Try again", action: "reload" }, sec: [nav("Back to evaluations", "workspace")] };
}

export { ds };
