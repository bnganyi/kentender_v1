// The Award record (AWD-CHG-001 v0.4 §9, §10.2–§10.3; boards D02, D03, D05,
// D06, D07, D07c, V01–V12, V15, V15s, V17–V21, V23, V23p, V24, V25) built
// from the server's GetAwardRecord answer. Which board a viewer sees follows
// the server's stage, cycle, outstanding issues and next step; the headline,
// journey and permitted actions are the server's. Board labels are the
// spec's own; every value is a recorded fact.
import { btn } from "../board/model.js";

const CONCLUSIONS = ["Recommend award", "No current recommendation"];
const has = (list, pred) => (list || []).some(pred);
const first = (list, pred) => (list || []).find(pred);

export function header(d, opts = {}) {
	const desc = [d.tender_reference, d.award, d.procuring_entity].filter(Boolean).join(" · ");
	const b = { hdr: { title: d.tender_title, desc }, kicker: "Award record", guidance: d.guidance };
	if (d.stage === "Closed" || d.cancelled) b.chip = ["is-critical", "Closed"];
	return { ...b, ...opts };
}

function reportFacts(d) {
	const r = d.report || {};
	return [["Report", r.label], ["Received", r.received_at], ["Committee signatures", r.signatures], ["Valid until", r.valid_until]];
}

function recSection(d) {
	const r = (d.report || {}).recommended;
	if (!r) return { t: "Recommendation", sec: true, d: [["Recommendation", "No current recommendation"]] };
	return { t: "Recommendation", sec: true, d: [["Recommendation", d.report.recommendation]], f: [["Supplier", r.supplier], ["Bid", r.bid], ["Bid version", r.bid_version],
		["Quantity", r.quantity], ["Submitted tender sum", r.submitted], ["Evaluated amount", r.evaluated], ["Warranty", r.warranty]] };
}

function opinionFields(d, form) {
	return [{ label: "Conclusion", radio: CONCLUSIONS, name: "conclusion" }, { label: "Reason", area: true, name: "reason" }];
}

const opinionActs = (d, extra = []) => [...extra, btn("Save draft", "save-opinion"), btn("*Sign opinion", "sign-opinion", {}, { disabled: !d.actions.sign_opinion })];

function discs(d, list) {
	const lines = {
		"Evaluation report": () => [`${d.report.label}, received ${d.report.received_at}`, `Committee signatures: ${d.report.signatures}`, `Outcome: ${d.report.outcome}`,
			d.report.reason].filter(Boolean).concat((d.report.dissent || []).length
				? d.report.dissent.map((x) => `Dissent recorded by ${x.member}, ${x.at}: ${x.statement}`) : ["No member recorded a dissent."]),
		"Bid comparison": () => (d.report.comparison || []).map((r) => `${r.position} · ${r.tenderer} · submitted ${r.submitted} · evaluated ${r.amount}`),
		"Outstanding issues": () => (d.outstanding || []).map((o) => `${o.title} — ${o.owner}`).concat(d.outstanding && d.outstanding.length ? [] : ["No outstanding issue."]),
		History: () => (d.history || []).flatMap((c) => [`Decision cycle ${c.cycle}: ${c.stage}${c.outcome ? ` — ${c.outcome}` : ""}`]
			.concat((c.opinions || []).map((o) => `${o.label}: ${o.state}${o.signed ? ` — ${o.signed}` : ""}`))
			.concat((c.decisions || []).map((x) => `${x.label} ${x.version}: ${x.outcome} — ${x.by}, ${x.at}`))),
		"Professional opinion": () => { const o = d.opinion.signed; return o ? [o.label, o.signed, o.conclusion, o.reason] : []; },
		"Notice preview": () => (d.notices.preview || []).map((p) => p.label || p.problem),
	};
	return list.map((t) => {
		const x = typeof t === "string" ? { t } : t;
		return { ...x, lines: (lines[x.t] || (() => []))() };
	});
}

const restrictionDisc = (d) => ({ t: "Outstanding issues", a: d.actions.record_restriction ? btn("Record restriction", "dialog", { name: "record-restriction" }) : null });

function outstandingIssue(d, pred) {
	return first(d.outstanding, (o) => o.issue && pred(o));
}

// -- which board this viewer is on ----------------------------------------------------
export function screenOf(d) {
	if (d.technical) return "technical";
	const v = d.viewer || {};
	const a = (d.guidance || {}).answer || {};
	const h = a.headline || "";
	if (d.cancelled) return "cancelled";
	if (d.stage === "Closed") return has(d.outstanding, (o) => o.type === "Source correction") && v.hop ? "closed-correction" : "no-award";
	if (d.stage === "Opinion") {
		if (d.cycle.awaiting_report) return "awaiting";
		if (has(d.outstanding, (o) => o.subtype === "Incomplete source")) return "source";
		if (has(d.outstanding, (o) => o.subtype === "Rules unverified")) return "rules";
		if (has(d.outstanding, (o) => o.subtype === "Status unavailable")) return "status";
		const w = d.opinion.working;
		if (w && w.state === "Signing" && w.signing_outcome && w.signing_outcome !== "Accepted/Verified") return "signing";
		if (!v.hop) return "opinion-read";
		if (d.returned) return "returned";
		if (h === "Tender validity has expired. No award can proceed.") return "expired";
		if (d.report.tie) return "tie";
		if (d.cycle.number > 1 || d.report.version > 1) return "corrected";
		return "opinion";
	}
	if (d.stage === "Decision") {
		if (!v.ao) return "decision-read";
		if (d.actions.decide_correction) return (d.opinion.signed || {}).conclusion === "Recommend award" ? "correction-positive" : "correction-decision";
		return "decision";
	}
	if (d.stage === "Notices") {
		if (d.actions.authorise_revised) return "revised-ready";
		if (has(d.outstanding, (o) => o.subtype === "Revised notice treatment")) return "revised-held";
		if (has(d.outstanding, (o) => o.subtype === "Notice delivery")) return "delivery-failure";
		return "notices";
	}
	if (d.stage === "Sent to Contracting") return has(d.outstanding, (o) => o.type === "Review/order" && o.holds) && v.hop ? "hold" : "delivered";
	// Waiting to proceed
	if (v.hop && has(d.outstanding, (o) => o.type === "Review/order" && o.holds)) return "hold";
	if (v.ao && d.actions.correction_proposals) return "correction-proposal";
	if (v.hop) {
		if (has(d.outstanding, (o) => o.type === "Source correction" && !o.proposal)) return "correction-review";
		if (has(d.outstanding, (o) => o.subtype === "Declined" && !o.proposal)) return "declined";
		if (has(d.outstanding, (o) => o.subtype === "No response" && !o.proposal)) return "no-response";
		if (has(d.outstanding, (o) => o.subtype === "Validity expired" && !o.proposal)) return "expired-after";
		if (has(d.outstanding, (o) => o.type === "Debrief")) return "request";
	}
	if (h.startsWith("Contracting is unavailable")) return "receiver-down";
	return "wait";
}

// -- the boards --------------------------------------------------------------------
const BUILD = {
	opinion: (d) => header(d, { sec: [{ t: "Evaluation report", sec: true, f: reportFacts(d) }, recSection(d), { t: "Professional opinion", fld: opinionFields(d) }],
		act: opinionActs(d, [btn("Return report", "dialog", { name: "return-report" }, { disabled: !d.actions.return_report })]), place: "decision",
		disc: discs(d, ["Evaluation report", "Bid comparison", restrictionDisc(d), "History"]) }),
	returned: (d) => header(d, { sec: [{ t: "Accounting Officer’s comments", d: [["Comment", d.returned.comment]] }, { t: "Professional opinion", fld: opinionFields(d) }],
		act: opinionActs(d, [btn("Return report", "dialog", { name: "return-report" }, { disabled: !d.actions.return_report })]), place: "decision", disc: discs(d, ["History"]) }),
	source: (d) => header(d, { sec: [{ t: "Evaluation report", sec: true, f: reportFacts(d) }] }),
	expired: (d) => header(d, { sec: [{ t: "Evaluation report", sec: true, f: reportFacts(d) }, { t: "Professional opinion", fld: opinionFields(d) }],
		act: opinionActs(d, [btn("View evaluation report", "view", { what: "report" })]), place: "decision" }),
	tie: (d) => header(d, { sec: [{ t: "Evaluation result", tbl: { h: ["Tenderer", "Amount", "Position"], n: [1, 2], r: (d.report.comparison || []).map((r) => [r.tenderer, r.amount, r.position]) },
		p: [d.report.reason, "Negotiation is outside MVP 1."].filter(Boolean) }, { t: "Professional opinion", fld: opinionFields(d) }],
		act: opinionActs(d, [btn("View evaluation report", "view", { what: "report" })]), place: "decision" }),
	corrected: (d) => header(d, { sec: [{ t: "Corrected report", sec: true, f: [["Decision cycle", String(d.cycle.number)], ["Report", d.report.label], ["Received", d.report.received_at],
		["Corrected result", d.report.recommended ? d.report.recommendation : "~is-attention:No current recommendation"]], d: [["Reason", d.report.reason]] },
		{ t: "Professional opinion", fld: opinionFields(d) }],
		act: opinionActs(d, [btn("View evaluation report", "view", { what: "report" }), btn("View prior decision", "view", { what: "prior-decision" })]), place: "decision" }),
	signing: (d) => header(d, { sec: [{ t: "Professional opinion", fld: opinionFields(d) }], act: [btn("Save draft", "save-opinion"), btn("View opinion", "view", { what: "opinion" })], place: "row" }),
	rules: (d) => header(d, { sec: [{ t: "Outstanding issue", f: [["Responsible officer", (outstandingIssue(d, (o) => o.subtype === "Rules unverified") || {}).owner]] }] }),
	status: (d) => header(d, { sec: [{ t: "Outstanding issue", f: [["Owner", (outstandingIssue(d, (o) => o.subtype === "Status unavailable") || {}).owner]] }],
		act: [btn("View outstanding issue", "view", { what: "issues" })], place: "row" }),
	awaiting: (d) => header(d, { sec: [{ t: "Correction instruction", f: [["Decision cycle", String(d.cycle.number)]], d: [["Reason", (d.cycle.authorising || {}).reason || ""]] }],
		act: [btn("View correction instruction", "view", { what: "instruction" }), btn("View prior decision", "view", { what: "prior-decision" })], place: "row" }),
	"opinion-read": (d) => header(d, { sec: [{ t: "Evaluation report", sec: true, f: reportFacts(d) }, recSection(d)], disc: discs(d, ["Evaluation report", "Bid comparison", "History"]) }),
	decision: (d) => header(d, { sec: [recSection(d), { t: "Professional opinion", sec: true, f: [["Opinion", d.opinion.signed.label]], p: [d.opinion.signed.signed], d: [["Reason", d.opinion.signed.reason]] },
		{ t: "Decision", fld: [{ label: "Decision reason", area: true, name: "decision_reason" }], d: [["Notice preview", (d.notices.preview || []).map((p) => p.label || p.problem).join("; ")]] }],
		act: [btn("Record no award", "dialog", { name: "record-no-award" }), btn("Return for correction", "dialog", { name: "return-for-correction" }),
			btn("*Award and notify bidders", "award", {}, { disabled: !d.actions.award_supported })], place: "decision",
		disc: discs(d, ["Professional opinion", "Evaluation report", "Notice preview"]) }),
	"decision-read": (d) => header(d, { sec: [recSection(d), { t: "Professional opinion", sec: true, f: [["Opinion", (d.opinion.signed || {}).label]], p: [(d.opinion.signed || {}).signed],
		d: [["Reason", (d.opinion.signed || {}).reason]] }] }),
	"correction-decision": (d) => header(d, { sec: [opinionTwo(d)], act: [btn("View prior decision", "view", { what: "prior-decision" }),
		btn("Return for correction", "dialog", { name: "correction-return" }), btn("*Record no award", "dialog", { name: "correction-no-award" })], place: "decision" }),
	"correction-positive": (d) => header(d, { sec: [opinionTwo(d, true), { t: "Revised notice", sec: true, f: [["Notice", d.revised.label], ["Reply by", d.revised.reply_by]], p: [d.revised.wait] },
		{ t: "Decision", fld: [{ label: "Decision reason", area: true, name: "decision_reason" }] }],
		act: [btn("Record no award", "dialog", { name: "correction-no-award" }), btn("Return for correction", "dialog", { name: "correction-return" }),
			btn("*Record corrected award and notify bidders", "corrected-award", {}, { disabled: !d.actions.award_supported })], place: "decision" }),
	"revised-held": (d) => header(d, { sec: [{ t: "Corrected award", f: corrFacts(d) }], act: [btn("View corrected decision", "view", { what: "decision" })], place: "row" }),
	"revised-ready": (d) => header(d, { sec: [{ t: "Corrected award", sec: true, f: corrFacts(d) }, { t: "Revised notice", f: [["Notice", d.revised.label], ["Reply by", d.revised.reply_by]], p: [d.revised.wait] }],
		act: [btn("View notice preview", "view", { what: "notices" }), btn("View corrected decision", "view", { what: "decision" }), btn("*Authorise revised notices", "authorise-revised")],
		place: "decision" }),
	"delivery-failure": (d) => header(d, { sec: [{ t: "Notices", tbl: { h: ["Recipient", "Channel", "Result", "Owner"], r: d.notices.recipients.filter((n) => n.status === "Failed")
		.map((n) => [n.recipient, n.channel, `~is-critical:${n.delivery}`, n.owner]) } }],
		act: [btn("View notice", "view", { what: "notices" }), btn("View delivery history", "view", { what: "delivery" })], place: "row" }),
	notices: (d) => header(d, { sec: [{ t: "Notices", tbl: { h: ["Recipient", "Channel", "Result", "Owner"], r: d.notices.recipients.map((n) => [n.recipient, n.channel,
		n.status === "Given" ? "~is-live:Given" : n.status === "Failed" ? `~is-critical:${n.delivery}` : n.status, n.owner || "—"]) } }],
		act: [btn("View notice", "view", { what: "notices" })], place: "row" }),
	hold: (d) => { const o = outstandingIssue(d, (x) => x.type === "Review/order" && x.holds) || {}; return header(d, { sec: [{ t: "Restriction",
		f: [["Responsible officer", o.owner], ["Basis for hold", `~is-attention:${o.basis}`]], d: [["Source", o.source]] }], act: [btn("View restriction", "view", { what: "issues" })], place: "row" }); },
	"correction-review": (d) => { const o = outstandingIssue(d, (x) => x.type === "Source correction" && !x.proposal) || {}; return header(d, { sec: [{ t: "Report correction", p: [o.reason] }],
		act: [btn("View original decision", "view", { what: "prior-decision" }), btn("*Review correction", "dialog", { name: "review-correction", issue: o.issue })], place: "decision" }); },
	"correction-proposal": (d) => { const o = outstandingIssue(d, (x) => x.proposal) || {}; const p = o.proposal || {}; const evaluation = p.outcome === "Request corrected evaluation";
		return header(d, { sec: [{ t: "Reported correction", d: [["Issue", o.reason], ["Proposal", p.next_action], ["Reason", p.reason]] }],
			act: evaluation ? [btn("View original decision", "view", { what: "prior-decision" }), btn("View correction", "view", { what: "issues" }),
				btn("*Request corrected evaluation", "correction", { outcome: "Request corrected evaluation", reason: p.reason })]
				: [btn("View original decision", "view", { what: "prior-decision" }), btn("Decline reconsideration", "correction", { outcome: "Decline reconsideration", reason: p.reason }),
					btn("*Authorise reconsideration", "correction", { outcome: "Authorise reconsideration", reason: p.reason })], place: "decision" }); },
	declined: (d) => { const r = d.notices.response || {}; const o = outstandingIssue(d, (x) => x.subtype === "Declined") || {}; return header(d, { sec: [{ t: "Supplier response",
		p: [`!Declined by ${r.by}, ${r.at}`], d: [["Reason", r.reason]], note: "The Accounting Officer must decide the next procurement action." }],
		act: [btn("View response", "view", { what: "response" }), btn("*Record next action", "dialog", { name: "record-next-action", issue: o.issue })], place: "decision" }); },
	"no-response": (d) => { const o = outstandingIssue(d, (x) => x.subtype === "No response") || {}; return header(d, { sec: [{ t: "Supplier response", f: [["Reply deadline", d.notices.batch.reply_deadline]] }],
		act: [btn("View notice", "view", { what: "notices" }), btn("*Record next action", "dialog", { name: "record-next-action", issue: o.issue })], place: "decision" }); },
	"expired-after": (d) => { const o = outstandingIssue(d, (x) => x.subtype === "Validity expired") || {}; return header(d, { sec: [{ t: "Outstanding issue", f: [["Responsible officer", o.owner]], d: [["Reason", o.reason]] }],
		act: [btn("View decision", "view", { what: "decision" }), btn("*Record next action", "dialog", { name: "record-next-action", issue: o.issue })], place: "decision" }); },
	request: (d) => requestBoard(d, first(d.correspondence, (c) => c.state === "Open")),
	wait: (d) => header(d, { sec: [{ t: "Acceptance and wait", p: waitLines(d), f: d.notices.earliest ? [["Earliest permitted date and time", d.notices.earliest]] : undefined }],
		act: [btn("View decision", "view", { what: "decision" }), btn("View notices", "view", { what: "notices" }), btn("View acceptance", "view", { what: "response" })], place: "row" }),
	"receiver-down": (d) => header(d, { act: [btn("View award package", "view", { what: "package" })], place: "row" }),
	delivered: (d) => header(d, { sec: [{ t: "Contracting", f: [["Received", d.package.received_at], ["Next", d.package.next], ["Contracting owner", d.package.owner]] }],
		act: [btn("View award package", "view", { what: "package" }), btn("Open Contracting", "view", { what: "contracting" })], place: "row" }),
	"no-award": (d) => header(d, { sec: [{ t: "Decision", d: [["Reason", (d.decision || {}).reason]] }],
		act: [btn("View decision", "view", { what: "decision" }), btn("View evaluation report", "view", { what: "report" })], place: "row" }),
	"closed-correction": (d) => { const o = outstandingIssue(d, (x) => x.type === "Source correction") || {}; return header(d, { sec: [{ t: `Decision cycle ${d.cycle.number} — Closed`, p: ["No award was made."] }],
		act: [btn("View prior decision", "view", { what: "prior-decision" }), btn("*Review correction", "dialog", { name: "review-correction", issue: o.issue })], place: "decision" }); },
	cancelled: (d) => header(d, { act: [btn("View cancellation", "view", { what: "cancellation" }), btn("View history", "view", { what: "history" })], place: "row" }),
};

function waitLines(d) {
	const out = [];
	const r = d.notices.response;
	if (r && r.response === "Accept") out.push(`+Supplier accepted, ${r.at}`);
	if (d.notices.batch && d.notices.batch.all_given) out.push("+All bidders have been notified");
	return out;
}

function opinionTwo(d, positive = false) {
	const o = d.opinion.signed || {};
	const f = [["Decision cycle", String(d.cycle.number)], ["Report", d.report.label], ["Opinion", o.label]];
	if (positive && d.report.recommended) f.push(["Amount", d.report.recommended.submitted]);
	const conclusion = o.conclusion === "Recommend award" && d.report.recommended ? `Recommend award to ${d.report.recommended.supplier}` : o.conclusion;
	return { t: o.label || "Professional opinion", f, p: [o.signed], d: [["Conclusion", conclusion], ["Reason", o.reason]] };
}

function corrFacts(d) {
	const x = d.decision || {};
	return [["Decision cycle", String(d.cycle.number)], ["Decision", x.label], ["Supplier", x.supplier], ["Amount", x.amount]];
}

export function requestBoard(d, c) {
	if (!c) return header(d, { sec: [{ t: "Request", empty: "Not found" }] });
	if (c.state === "Closed") {
		return header(d, { next: { k: "done", h: "This request is closed." }, guidance: { answer: { kind: "done", label: "Done", headline: "This request is closed.", blockers: [], fixes: [] },
			journey: d.guidance.journey }, sec: [{ t: "Request", f: [["From", c.from], ["Closed", c.closed_at]], p: [c.text], d: [["Response", c.reply]] }],
			act: [btn("View correspondence", "view", { what: "correspondence" })], place: "row", screen: "request-closed" });
	}
	return header(d, { sec: [{ t: "Request", f: [["From", c.from]], p: [c.text], fld: [{ label: "Response", area: true, name: "reply" }] },
		{ t: "Acceptance and wait", sec: true, p: ["The required waiting period is still running."] }],
		act: [btn("Save reply", "save-reply", { request: c.request }), btn("*Send and close", "send-reply", { request: c.request })], place: "decision", request: c.request });
}

export function technicalBoard(d) {
	const op = (d.operations || []).filter((o) => o.status === "Open")[0] || (d.operations || [])[0] || {};
	return { hdr: { title: op.subject || "Technical work" }, kicker: "Technical work", screen: "technical",
		sec: [{ t: "Operation", f: [["Operation", (op.detail || "").replace(/^Operation: ([^.]*)\..*$/, "$1") || op.operation], ["Result", op.status === "Open" ? "Service unavailable" : "Resolved"],
			["Assigned to", d.holder_name || ""]] }],
		act: [btn("View service history", "view", { what: "service" }), btn("*Retry operation", "retry-operation")], place: "decision" };
}

export function recordBoard(d, ctx = {}) {
	if (d.technical) return technicalBoard(d);
	if (ctx.sub === "requests" && ctx.id) return { screen: "request", ...requestBoard(d, first(d.correspondence, (c) => c.request === ctx.id)) };
	const screen = screenOf(d);
	const build = BUILD[screen] || BUILD.wait;
	return { ...build(d), screen };
}

export { CONCLUSIONS };
