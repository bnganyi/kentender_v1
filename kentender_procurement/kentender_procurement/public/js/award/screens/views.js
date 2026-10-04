// Read-only views of retained versions (AWD-CHG-001 v0.4 §11: "Document/view/
// history actions open retained versions read-only"): /app/award/{id}/view/{what}.
// Nothing here writes; Back returns to the record.
import { btn } from "../board/model.js";
import { header } from "./record.js";

const back = () => btn("Back to award", "back");

function decisionFacts(x) {
	if (!x) return [["Decision", "No decision recorded"]];
	return [["Decision", `${x.label} (version ${x.version})`], ["Outcome", x.outcome], ["By", x.by], ["At", x.at], ["Supplier", x.supplier || "—"], ["Amount", x.amount || "—"]];
}

const VIEWS = {
	report: (d) => [{ t: "Evaluation report", f: [["Report", d.report.label], ["Received", d.report.received_at], ["Committee signatures", d.report.signatures],
		["Valid until", d.report.valid_until], ["Outcome", d.report.outcome]], d: [["Reason", d.report.reason]] },
		{ t: "Bid comparison", tbl: { h: ["Tenderer", "Submitted", "Evaluated", "Position"], n: [1, 2, 3], r: d.report.comparison.map((r) => [r.tenderer, r.submitted, r.amount, r.position]) } },
		{ t: "Report versions", tbl: { h: ["Report", "State", "Received"], r: d.report.versions.map((v) => [v.label, v.state, v.received_at]) } }],
	opinion: (d) => (d.opinion.all || []).map((o) => ({ t: o.label, f: [["State", o.state], ["Conclusion", o.conclusion || "—"], ["Author", o.author]],
		p: o.signed ? [o.signed].concat(o.proof_label ? [o.proof_label] : []) : [], d: [["Reason", o.reason || "—"]] })),
	decision: (d) => [{ t: "Decision", f: decisionFacts(d.decision), d: [["Reason", (d.decision || {}).reason || "—"]].concat((d.decision || {}).next_action ? [["Next action",
		`${d.decision.next_action} — ${d.decision.next_owner}`]] : []) }],
	"prior-decision": (d) => (d.history || []).filter((c) => c.cycle < d.cycle.number || d.stage === "Closed").flatMap((c) => (c.decisions || []).map((x) => ({ t: `Decision cycle ${c.cycle}`,
		f: decisionFacts(x), d: [["Reason", x.reason || "—"]] }))),
	instruction: (d) => [{ t: "Correction instruction", f: [["Decision cycle", String(d.cycle.number)], ["Instruction", (d.cycle.authorising || {}).outcome || "—"],
		["By", (d.cycle.authorising || {}).by || "—"], ["At", (d.cycle.authorising || {}).at || "—"]], d: [["Reason", (d.cycle.authorising || {}).reason || "—"]] }],
	notices: (d) => [{ t: "Notices", tbl: { h: ["Recipient", "Result", "Status", "Given"], r: d.notices.recipients.map((n) => [n.recipient, n.result, n.status, n.given_at || "—"]) },
		f: d.notices.batch ? [["Notice", d.notices.batch.label], ["Issued", d.notices.batch.issued_at], ["Reply by", d.notices.batch.reply_deadline || "—"]] : undefined }],
	delivery: (d) => [{ t: "Notices", tbl: { h: ["Recipient", "Contact", "Attempts", "Last attempt"], r: d.notices.recipients.map((n) => [n.recipient, n.contact, String(n.attempts), n.last_attempt]) } }],
	response: (d) => [{ t: "Supplier response", f: d.notices.response ? [["Response", d.notices.response.response], ["By", d.notices.response.by], ["At", d.notices.response.at]] : [["Response", "No response recorded"]],
		d: d.notices.response ? [["Wording", d.notices.response.wording]].concat(d.notices.response.reason ? [["Reason", d.notices.response.reason]] : []) : undefined,
		p: (d.notices.late || []).map((r) => `Received after the deadline: ${r.response} by ${r.by}, ${r.at}`) }],
	package: (d) => [{ t: "Contracting", f: d.package ? [["Package", d.package.id], ["Status", d.package.status], ["Received", d.package.received_at || "—"],
		["Delivery attempts", String(d.package.attempts)], ["Later updates", String(d.package.updates)]] : [["Package", "Not prepared yet"]] }],
	contracting: (d) => [{ t: "Contracting", f: [["Received", (d.package || {}).received_at || "—"], ["Next", (d.package || {}).next || "—"], ["Contracting owner", (d.package || {}).owner || "—"]],
		p: ["Contracting on this site is the test receiver: it records the receipt and the Prepare contract task only. No contract exists."] }],
	issues: (d) => (d.outstanding || []).map((o) => ({ t: o.title, f: [["Owner", o.owner], ["Type", o.type], ["Received", o.received_at || "—"]].concat(o.basis ? [["Basis for hold", o.basis]] : []),
		d: [["Reason", o.reason || "—"]].concat(o.source ? [["Source", o.source]] : []) })),
	history: (d) => (d.history || []).map((c) => ({ t: `Decision cycle ${c.cycle}`, f: [["Stage", c.stage], ["Outcome", c.outcome || "—"]],
		p: (c.opinions || []).map((o) => `${o.label}: ${o.state}`).concat((c.decisions || []).map((x) => `${x.label} ${x.version}: ${x.outcome} — ${x.by}, ${x.at}`)) })),
	cancellation: (d) => [{ t: "Decision", d: [["Reason", d.closed_reason || "This tender was cancelled. Award ended."]] }],
	correspondence: (d) => (d.correspondence || []).map((c) => ({ t: "Request", f: [["From", c.from], ["Received", c.requested_at], ["State", c.state]],
		p: [c.text], d: c.reply ? [["Response", c.reply]] : undefined })),
	service: (d) => [{ t: "Operation", tbl: { h: ["Issue", "Operation", "Status", "Opened"], r: (d.operations || []).map((o) => [o.issue, o.operation, o.status, o.opened_at]) } }],
};

export function viewBoard(d, what) {
	const sec = (VIEWS[what] || (() => []))(d) || [];
	const base = d.technical ? { hdr: { title: "Technical work" }, kicker: "Technical work" } : header(d, { guidance: null });
	return { ...base, sec: sec.length ? sec : [{ t: "Record", empty: "Nothing is recorded yet." }], act: [back()], place: "row", screen: `view-${what}` };
}
