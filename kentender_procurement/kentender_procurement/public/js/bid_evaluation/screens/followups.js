// Verification, opening updates, correction notices and support issues
// (EVL-CHG-001 v0.4 §9.9, §9.13; boards D08-DD, D08-DD-FREEZE, D08-DD-SIGN,
// D08-SUPPLEMENT, D08-SUPPLEMENT-SENT, D08-SUPPLEMENT-HOP, D08-CORRECTION,
// D08-CORRECTION-HOP). Opening a record never clears a task; only the
// recorded command does.
import { ev, f, fi, kv, ra, tb } from "../board/model.js";
import { cmd, guidance, nav } from "./common.js";

function hhmm(when) {
	const m = /(\d{2}:\d{2})/.exec(when || "");
	return m ? m[1] : when || "";
}

export function verification(ctx) {
	const { data, user } = ctx;
	const ver = (data.work || {}).verification;
	if (!ver) return null;
	const facts = f(["Scope", ver.scope], ["Participants", ver.participants.map((x) => (x.user === ver.lead ? `${x.name} (lead)` : x.name)).join(" and ")]);
	const evidence = (ctx.bid && ctx.bid.requirements || []).filter((r) => /experience/i.test(r.label)).flatMap((r) => r.evidence);
	const evd = evidence.length ? ev(evidence.map((e) => ({ label: e.name, action: "evidence", args: { digest: e.digest } }))) : null;
	const observed = ver.observations.map((o) => o.user);
	const mine = ver.participants.some((x) => x.user === user);
	const base = { title: data.title, desc: data.tender, guidance: guidance(data) };
	if (ver.report_state === "Draft" && mine && !observed.includes(user)) {
		return { ...base, guidance: guidance(data, { headline: "Record the supplier verification findings." }),
			blocks: [facts, evd, fi("Findings", "", { area: true, req: true, rows: 3, name: "findings" })].filter(Boolean),
			pri: cmd("Save findings", "record_verification_findings", { fields: ["findings"] }) };
	}
	const findings = tb(["Participant", "Recorded", "Observation"], ver.observations.map((o) => [o.name, hhmm(o.recorded), o.findings]), { title: "Verification findings", sec: true });
	if (ver.report_state === "Draft" && user === ver.lead && observed.length >= ver.participants.length) {
		return { ...base, guidance: guidance(data, { headline: "Send the verification report to its participants for signing." }), blocks: [facts, findings, evd].filter(Boolean),
			pri: cmd("Send verification report for signing", "send_verification_for_signing"), sec: [],
			cons: "Each participant will sign the same report and its required pages." };
	}
	const sigs = tb(["Participant", "Signature"], ver.signatures.map((s) => [s.name, s.signed ? `Signed ${hhmm(s.signed)}` : s.user === user ? "Your signature needed" : "Awaiting signature"]), { title: "Signatures", sec: true });
	if (ver.report_state === "Frozen" && (ver.my_targets || []).length) {
		return { ...base, guidance: guidance(data, { headline: "Review and sign verification report" }),
			blocks: [f(["Report", "Verification report 1 · frozen"]), facts, tb(["Participant", "Observation"], ver.observations.map((o) => [o.name, o.findings]), { title: "Findings", sec: true }), sigs],
			pri: cmd("Sign verification report", "sign_verification_report") };
	}
	return { ...base, blocks: [f(["Report", `Verification report · ${ver.report_state.toLowerCase()}`]), facts, findings, ver.report_state !== "Draft" ? sigs : null].filter(Boolean),
		sec: [nav("Back to evaluation", [])] };
}

export function update(ctx) {
	const { data, id, user } = ctx;
	const u = ((data.work || {}).updates || []).find((x) => x.name === id);
	if (!u) return null;
	const d = u.detail || {};
	const sent = u.delivered_context === "After delivery";
	const delivery = (data.work || {}).delivery || {};
	const hop = delivery.recipient_user === user;
	const src = sent ? f(["Source", `Opening record supplement, ${u.received}`], ["Kind", d.kind || ""], ["Text", d.text || d.note || ""]) : f(["Recorded by", `${u.author}, ${hhmm(u.received)}`], ["Kind", d.kind || ""], ["Note", d.text || d.note || ""]);
	const report = f(["Report", `Report ${delivery.report_number || 1} · delivered`]);
	if (hop && sent) {
		return { title: data.title, desc: data.tender, guidance: guidance(data, { headline: "Review the opening update alongside the delivered report." }),
			blocks: [f(["Task", `Review opening update for ${data.tender}`]), src, report],
			pri: u.head_review_state === "Open" ? cmd("Open new evidence", "record_head_review", { values: { item: u.name } }) : null,
			sec: [nav("Open report", ["report", "preview"]), { label: "Return for correction", action: "dialog", args: { name: "return" } }] };
	}
	const blocks = [src];
	if (sent) blocks.push(report);
	const pending = !u.impact || u.impact === "Pending";
	if (pending && data.viewer.eligible) {
		blocks.push(ra("Impact", ["No effect on findings", "Findings need review"], 0, { name: "impact" }), fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" }));
		return { title: data.title, desc: data.tender, guidance: guidance(data, { headline: sent ? "Review the opening update." : "Review the correction added to the opening record." }), blocks,
			pri: cmd("Record impact", "assess_opening_update", { values: { source_event: u.name, compose: "impact" }, fields: ["reason"] }), sec: [{ label: "View opening record", action: "nav-opening" }] };
	}
	blocks.push(f(["Impact", u.impact || "Pending"], ["Reason", u.impact_reason || ""]));
	return { title: data.title, desc: data.tender, guidance: guidance(data), blocks, sec: [nav("Back to evaluation", [])] };
}

export function correction(ctx) {
	const { data, user, report } = ctx;
	const work = data.work || {};
	const delivery = work.delivery || {};
	const decision = f(["Report", `Report ${(report && report.version_number) || 1} · delivered`], ["Downstream decision", (report && report.downstream_label) || (report && report.downstream) || ""]);
	if (delivery.recipient_user === user) {
		const notice = (work.notices || []).filter((x) => x.head_review_state === "Open").slice(-1)[0] || (work.notices || []).slice(-1)[0];
		if (!notice) return null;
		return { title: data.title, desc: data.tender, guidance: guidance(data, { headline: "Review the report correction alongside the delivered report." }),
			blocks: [f(["Task", `Review report correction for ${data.tender}`]), kv([["Recorded by", notice.recorded_by_name || ""], ["Reason", notice.reason], ["Correction", notice.correction]], { title: "Correction notice", sec: true }), decision],
			pri: notice.head_review_state === "Open" ? cmd("Open new evidence", "record_head_review", { values: { item: notice.name } }) : null, sec: [nav("Open report", ["report", "preview"])] };
	}
	return { title: data.title, desc: data.tender, guidance: guidance(data, { headline: `Record the report correction for ${delivery.recipient_name || "the Head of Procurement"}.` }),
		blocks: [decision, fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" }), fi("Correction", "", { area: true, req: true, rows: 2, name: "correction" })],
		pri: cmd("Send correction notice", "record_correction_notice", { fields: ["reason", "correction"], after: [] }), sec: [nav("Open report", ["report", "preview"])] };
}

export function issue(ctx) {
	const { data } = ctx;
	const issues = (data.work || {}).issues || [];
	return { title: data.title, desc: data.tender, guidance: guidance(data),
		blocks: issues.length ? issues.map((i) => kv([["Recorded", i.opened], ["Assigned to", `${(i.holders || []).join(", ") || "Technical support"}, Technical support`], ["Reason", i.safe_detail || i.subject], ["Status", i.status]], { title: "Support issue", sec: true }))
			: [f(["Support issue", "No support issue is recorded for this evaluation."])],
		sec: [nav("Back to evaluation", [])] };
}
