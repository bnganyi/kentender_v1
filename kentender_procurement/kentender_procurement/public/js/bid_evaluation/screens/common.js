// Shared compositions for the Bid Evaluation screens (EVL-CHG-001 v0.4 §9),
// the live counterparts of the artboard kit's own (`evl-kit.js`: recHead,
// summary, sections, sigs, roster, attend, comp). Every value comes from the
// server's reads; nothing here decides what a viewer may see or do.
import { ds, f, kv, lk, n, tb, button, initials } from "../board/model.js";

export const nav = (label, to, o) => button(label, "nav", { args: { to: [].concat(to || []) }, ...(o || {}) });
// A button that runs a command: `fields` names the form values it sends,
// `values` fixed arguments; `versioned`/`reportVersion` send the version the
// viewer was shown; `after` navigates on success; `close` closes the dialog;
// `reuseKey` reconciles the same attempt; `testid` names the button.
export const cmd = (label, method, o) => {
	const { fields, values, after, testid, ...rest } = o || {};
	return button(label, "cmd", { args: { method, fields: fields || [], values: values || {}, after: after || null, ...rest }, testid: testid || "" });
};
export const dialog = (label, name, o) => button(label, "dialog", { args: { name }, ...(o || {}) });

export function money(currency, value) {
	if (value === null || value === undefined || value === "") return "";
	const num = Number(value);
	if (!Number.isFinite(num)) return String(value);
	return `${currency || "KES"} ${num.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Everyone named on this evaluation, for the boards' avatar initials.
export function peopleOf(data) {
	const out = {};
	const add = (name) => { if (name) out[name] = initials(name); };
	const c = (data && data.committee) || {};
	(c.members || []).forEach((m) => add(m.name));
	if (c.secretary) add(c.secretary.name);
	return out;
}

// The delivered versions of the report, for a reader outside the committee (OVS-CHG-001 v0.6 §7): each is
// readable on its own, and the one on screen is marked. Absent when only one version was ever delivered.
export function versionsBlock(data, current) {
	const list = ((data.delivered_report || {}).versions) || [];
	if (list.length < 2) return null;
	return tb(["Report", "Sent", "Review", ""], list.map((v) => [`Report ${v.version_number}${v.report === current ? " (shown)" : ""}`, v.delivered, v.review_state || "",
		v.report === current ? "" : { label: "View", action: "nav", args: { to: ["report", v.report] }, testid: `evl-version-${v.version_number}` }]), { title: "Report versions", testid: "evl-versions", sec: true });
}

export function head(data, o) {
	return { title: data.title, desc: data.tender, ...(o || {}) };
}

export function guidance(data, o) {
	const answer = o && o.headline ? { ...(data.guidance || {}), headline: o.headline, sentence: o.sentence || "" } : data.guidance;
	return { answer, journey: o && o.journey === false ? null : data.tracker };
}

export function recordTabs(tab) {
	return { tabs: [{ label: "Results", action: "nav", args: { to: [] } }, { label: "Committee record", action: "nav", args: { to: ["record"] } }], tab };
}

// The bid comparison (E.comp): Bidder · Eligibility · Technical compliance ·
// Submitted total · Evaluated total · Position · Action.
export function comparisonTable(data, o) {
	const table = data.comparison || { rows: [] };
	const action = !(o && o.noAction);
	const rows = table.rows.map((r) => [
		r.bidder, r.eligibility, r.technical, money(r.currency, r.submitted_total),
		/^[0-9.]+$/.test(String(r.evaluated_total || "")) ? money(r.currency, r.evaluated_total) : r.evaluated_total || "",
		String(r.position || ""),
		action ? { label: "Review bid", action: "nav", args: { to: ["bid", r.bid] }, testid: `evl-review-${r.bid}` } : "—",
	]);
	return tb(["Bidder", "Eligibility", "Technical compliance", "Submitted total", "Evaluated total", "Position", "Action"], rows, {
		title: "Bid comparison", testid: "evl-comparison", ...(o || {}),
	});
}

export function sourceDisclosure(data) {
	const s = data.source;
	if (!s) return null;
	const lines = [s.opening_completed ? `Opening completed ${s.opening_completed}` : "", s.submitted_version ? `Submitted Version ${s.submitted_version}` : ""].filter(Boolean);
	return ds("Opening and source record", lines, { links: [{ label: "View opening record", action: "nav-opening" }], testid: "evl-source" });
}

export function rosterTable(data, o) {
	const c = data.committee || {};
	const rows = (c.members || []).map((m) => [m.name, m.department, m.capacity]);
	if (c.secretary) rows.push([c.secretary.name, "Procurement", "Secretary — not a voting or signing member"]);
	return tb(["Person", "Department", "Capacity"], rows, { title: "Committee", sec: true, testid: "evl-roster", ...(o || {}) });
}

export function attendanceTable(session, data, o) {
	const c = data.committee || {};
	const byUser = {};
	(session.attendance || []).forEach((a) => { byUser[a.user] = a; });
	const rows = (c.members || []).map((m) => [m.name, m.capacity, mark(byUser[m.user], "Joined")]);
	if (c.secretary && !(o && o.membersOnly)) rows.push([c.secretary.name, "Secretary", mark(byUser[c.secretary.user], "Present")]);
	return tb(["Person", "Capacity", "Attendance"], rows, { title: "Attendance", sec: true, testid: "evl-attendance" });
}

function hhmm(when) {
	const m = /(\d{2}:\d{2})/.exec(when || "");
	return m ? m[1] : when || "";
}

function mark(a, word) {
	if (!a) return "Not joined";
	if (!a.present && a.left) return `Left ${hhmm(a.left)}`;
	return `${word} ${hhmm(a.joined)}`;
}

export function attendanceLines(session) {
	return (session.attendance || []).map((a) => (a.left ? `${a.name} joined ${hhmm(a.joined)}, left ${hhmm(a.left)}` : `${a.name} ${a.capacity === "Secretary" ? "present from" : "joined"} ${hhmm(a.joined)}`));
}

export function sectionLinks() {
	return lk(["Tender and committee", "Bid findings", "Financial comparison", "Clarifications and committee record", "Recommendation and reasons"].map((t) => ({
		label: t, action: "nav", args: { to: ["report", "preview"], anchor: t } })), { title: "Report sections", sec: true, testid: "evl-sections" });
}

export function signaturesTable(signatures, user, data, o) {
	const cap = {};
	(((data && data.committee) || {}).members || []).forEach((m) => { cap[m.user] = m.capacity; });
	const rows = (signatures || []).map((s) => [s.name, cap[s.member] || "Member", s.signed ? `Signed ${hhmm(s.signed)}` : s.member === user ? "Your signature needed" : "Awaiting signature"]);
	return tb(["Member", "Capacity", "Signature"], rows, { title: "Signatures", sec: true, testid: "evl-signatures", ...(o || {}) });
}

// The report summary (E.summary) from the generated content.
export function summaryBlock(content) {
	const s = (content && content.summary) || {};
	const rec = (content && content.recommendation) || {};
	const rows = [];
	if (rec.recommended) {
		rows.push(["Recommendation", rec.recommended.bidder], ["Evaluated total", s.evaluated_total]);
	} else if (s.outcome) {
		rows.push([rec.outcome === "No agreed recommendation" || rec.outcome === "No responsive bids" ? "Recommendation" : "Outcome", s.outcome]);
		if (s.reason) rows.push(["Reason", s.reason]);
	} else {
		rows.push(["Recommendation", "Provisional comparison — no recommendation yet"]);
	}
	const f0 = ((content && content.bid_findings) || [])[0];
	if (f0 && rec.recommended) {
		rows.push(["Eligibility", f0.groups ? f0.groups["EVG-ELIGIBILITY"] || "" : ""], ["Technical compliance", f0.groups ? f0.groups["EVG-TECHNICAL-COMPLIANCE"] || "" : ""]);
	}
	const clar = ((content && content.clarifications_and_record) || {}).clarifications || [];
	const closed = clar.filter((c) => c.status === "Closed");
	if (closed.length) rows.push(["Clarification", closed.map((c) => `${c.disposition_result === "Meets" ? "Resolved" : c.disposition_result || c.disposition} — ${c.disposition_reason}`).join(" ")]);
	if (s.diligence) rows.push(["Due diligence", s.diligence]);
	const funding = rec.funding;
	if (funding && funding.qualification) {
		rows.push(["Available funding", money("KES", funding.available)], ["Shortfall", money("KES", funding.shortfall)],
			["Qualification", funding.qualification]);
	}
	(s.qualifications || []).filter((q) => !funding || q !== funding.qualification).forEach((q) => rows.push(["Qualification", q]));
	return kv(rows, { title: "Summary", testid: "evl-summary" });
}

export function conditionNotices(data) {
	const c = data.conditions || {};
	const out = [];
	if (c.validity_expired) out.push(n("warning", `Tender validity ended ${c.validity_end}; no extension recorded.`));
	else if (c.overdue) out.push(n("warning", "The evaluation deadline has passed."), f(["Evaluation deadline", c.evaluation_deadline], ["Tender validity", "Tender validity has not expired."]));
	return out;
}

export function ownerEvent(data, kind) {
	return ((data.work || {}).owner_events || []).filter((e) => e.kind === kind).slice(-1)[0] || null;
}

// S-STALE-RECORD: the record changed since this viewer loaded it. The page and
// the unsent form are kept; the one action is Refresh (AGENTS.md §6.4).
export const STALE = "This record changed while you were working. Refresh it and try again.";
export function staleBoard(board) {
	return { ...board, blocks: [n("warning", STALE), ...(board.blocks || [])], pri: { label: "Refresh", action: "refresh-stale" }, sec: [], cons: "" };
}
