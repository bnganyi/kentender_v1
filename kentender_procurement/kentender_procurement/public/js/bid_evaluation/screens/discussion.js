// Committee discussion (EVL-CHG-001 v0.4 §9.6, §9.7, §9.9, §9.13; boards
// D05, D05-CHAIR, D05-START, D05-JOIN, D05-MEMBER, D05-DISAGREE, D05-ABSENT,
// D05-ABSENT-CHAIR, D05-ABSENT-MEMBER, D05-CONCLUSION, D05-CONCLUSION-Q,
// D06-OUTCOME, D06-NO-REPLY, D06-LATE-REVIEW, D06-CHANGED-OFFER,
// D08-VERIFY-PLAN, D08-VERIFY-OUTCOME, D08-VERIFY-NEG).
//
// One screen for the whole live session; what each person sees follows the
// server's attendance: a member who is not present joins; the secretary
// records notes; the chair, once the whole current eligible committee is
// present, records the collective decision. The decision form is chosen from
// the record (a reply or overdue request to dispose, a signed verification
// report, a proposed clarification); the chair can switch it locally.
import { at, cb, ds, ev, f, fi, kv, n, sg, tb } from "../board/model.js";
import { attendanceLines, attendanceTable, cmd, comparisonTable, dialog, guidance, nav } from "./common.js";

export const DECISIONS = [
	{ key: "conclusion", label: "Record conclusion" },
	{ key: "clarification", label: "Authorise clarification" },
	{ key: "verification", label: "Record verification plan" },
	{ key: "basis", label: "Record due-diligence basis" },
];

function requirementOf(bid, key) {
	return ((bid && bid.requirements) || []).find((r) => r.requirement_key === key) || null;
}

function subjectOf(ctx) {
	const { data, bid } = ctx;
	const item = (data.attention || [])[0] || focusItem(ctx);
	const session = (data.work || {}).session || {};
	const r = item ? requirementOf(bid, item.requirement_key) : null;
	const facts = [["Subject", session.subject || (item && item.subject) || ""]];
	if (r) facts.push(["Requirement", r.checks.map((c) => c.required).filter(Boolean)[0] || r.label], ["Response", [...new Set(r.checks.filter((c) => c.field !== "compliance").map((c) => c.offered).filter(Boolean))].join("; ")]);
	return { block: f(...facts), item, requirement: r };
}

// The requirement the session is about: an open item, a clarification being
// disposed, or the verified requirement.
export function focusItem(ctx) {
	const { data } = ctx;
	const open = (data.attention || [])[0];
	if (open) return { evaluation_bid: open.evaluation_bid, requirement_key: open.requirement_key, subject: open.subject };
	const c = replyToDispose(data);
	if (c) return { evaluation_bid: c.evaluation_bid, requirement_key: c.requirement_key, subject: "" };
	return null;
}

export function replyToDispose(data) {
	return ((data.work || {}).clarifications || []).find((c) => c.status === "Sent" && (c.reply || c.overdue)) || null;
}

function evidenceBlock(requirement) {
	const files = (requirement && requirement.evidence) || [];
	return files.length ? ev(files.map((e) => ({ label: e.name, action: "evidence", args: { digest: e.digest, bid: requirement.bid } }))) : null;
}

function defaultDecision(data) {
	const verification = (data.work || {}).verification;
	if (replyToDispose(data)) return "reply";
	if (verification && verification.report_state === "Signed" && verification.status === "Current") return "verification-outcome";
	if (((data.work || {}).notes || []).length) return "clarification";
	return "conclusion";
}

export function discussion(ctx) {
	const { data, user, form } = ctx;
	const work = data.work || {};
	const session = work.session;
	if (!session) return null;
	const v = data.viewer;
	const here = (session.present || []).includes(user);
	const left = (session.attendance || []).filter((a) => !a.present && a.left && (session.missing || []).includes(a.user));
	const subject = subjectOf(ctx);
	const evd = evidenceBlock(subject.requirement ? { ...subject.requirement, bid: (subject.item || {}).evaluation_bid } : null);
	const att = attendanceTable(session, data);
	const absentNotice = left.length ? n("warning", "All members of the current eligible committee must be present to record this conclusion.", `${left.map((a) => a.name).join(" and ")} must rejoin.`) : null;
	const base = { title: "Committee discussion", desc: `${data.tender} · ${session.started ? session.started.split(",")[0] : ""}`, guidance: guidance(data) };

	if (!here) {
		// D05-JOIN / D05-ABSENT-MEMBER
		return { ...base, blocks: [absentNotice, att, subject.block, evd].filter(Boolean), pri: cmd("Join discussion", "join_discussion") };
	}
	if (v.secretary) {
		const note = [fi("Discussion note", "", { area: true, rows: 2, name: "note" })];
		if ((session.missing || []).length) {
			// D05-ABSENT
			return { ...base, blocks: [absentNotice || n("warning", "All members of the current eligible committee must be present to record this conclusion.", `${session.missing_names.join(" and ")} must join.`),
				subject.block, evd, ...note, ds("View attendance", attendanceLines(session))].filter(Boolean),
			pri: cmd("Save discussion note", "record_note", { values: { subject: session.subject }, fields: ["note", "reason"] }) };
		}
		// D05
		return { ...base, blocks: [att, subject.block, evd, ...note, fi("Reason", "", { area: true, rows: 2, name: "reason" }),
			ds("Earlier discussion", `Discussion started by ${session.started_by}, ${session.started}.`)].filter(Boolean),
		pri: cmd("Save discussion note", "record_note", { values: { subject: session.subject }, fields: ["note", "reason"] }) };
	}
	if (v.chair) {
		if ((session.missing || []).length) {
			// D05-START / D05-ABSENT-CHAIR
			return { ...base, blocks: [absentNotice, att, subject.block, evd].filter(Boolean),
				sec: left.length ? [cmd("End discussion", "end_discussion")] : [cmd("Leave discussion", "leave_discussion"), cmd("End discussion", "end_discussion")] };
		}
		return chairDecision(ctx, { base, att, subject, evd, decision: form.decision || defaultDecision(data) });
	}
	// A member who is present: D05-MEMBER, or waiting on the chair.
	const recorded = (work.conclusions || []).filter((c) => c.session === session.id).slice(-1)[0];
	const blocks = [att, subject.block];
	if (recorded) {
		blocks.push(kv([["Conclusion", `${recorded.kind === "Clarification" ? "Clarification authorised" : recorded.kind} by ${recorded.recorded_by_name}, ${recorded.at_time}`],
			...(recorded.question ? [["Question", recorded.question]] : []), ["Reason", recorded.reason]], { title: "Recorded conclusion", sec: true }));
		return { ...base, blocks, pri: dialog("Record disagreement", "disagree", { args: { name: "disagree", conclusion: recorded.name } }), sec: [cmd("Leave discussion", "leave_discussion")] };
	}
	if (evd) blocks.push(evd);
	return { ...base, blocks, sec: [cmd("Leave discussion", "leave_discussion")] };
}

function switcher(current) {
	return { k: "links", links: DECISIONS.filter((d) => d.key !== current).map((d) => ({ label: d.label, action: "set", args: { name: "decision", value: d.key } })), testid: "evl-decision-switch" };
}

function chairDecision(ctx, { base, att, subject, evd, decision }) {
	const { data, form } = ctx;
	const item = subject.item || {};
	const work = data.work || {};
	const end = cmd("End discussion", "end_discussion");
	if (decision === "reply") {
		// D06-OUTCOME / D06-NO-REPLY: the reply is Considered (or there is none)
		// and its result is recorded; D06-LATE-REVIEW / D06-CHANGED-OFFER: a late
		// reply, or a reply that changes the offer, gets its disposition instead.
		const c = replyToDispose(data);
		const late = !!(c.reply && c.reply.timeliness === "Late");
		const excluded = form.disposition === "Excluded change";
		const title = `${subject.requirement ? subject.requirement.label : "Requirement"} clarification`;
		const reason = fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" });
		const record = (disposition, fields) => cmd("Record reply outcome", "record_reply_disposition", { values: { clarification: c.name, disposition, compose: "disposition-result" }, fields });
		const g = guidance(data, { headline: "Record how the reply affects the finding." });
		if (!c.reply) {
			return { ...base, title, guidance: g, blocks: [kv([["Question", c.question], ["Reply deadline", c.deadline]], { title: "Committee question", sec: true }),
				f(["Reply", "No reply received"], ["Status", "Reply overdue"]), sg("Result", ["Meets", "Does not meet", "Needs review"], -1, { name: "result" }), reason],
			pri: record("No reply", ["result", "reason"]), sec: [end] };
		}
		if (late || excluded) {
			const options = late ? ["Not considered", "Considered"] : ["Excluded change", "Considered"];
			const blocks = [kv([["Question", c.question], ["Reply deadline", c.deadline], ["Reply", c.reply.body], ["Received", late ? `Received late, ${c.reply.received}` : c.reply.received]],
				{ title: "Committee question and reply", sec: true }),
				fi("Disposition", "", { select: true, req: true, name: "disposition", options: options.map((x) => ({ value: x, label: x })) })];
			if (form.disposition === "Considered") blocks.push(sg("Result", ["Meets", "Does not meet", "Needs review"], -1, { name: "result" }));
			blocks.push(reason);
			if (!late) blocks.push({ k: "links", links: [{ label: "Consider the reply", action: "set", args: { name: "disposition", value: "Considered" } }] });
			return { ...base, title, guidance: g, blocks, pri: record(form.disposition || options[0], ["result", "reason"]), sec: [end] };
		}
		return { ...base, title, guidance: g,
			blocks: [kv([["Question", c.question], ["Reply deadline", c.deadline]], { title: "Committee question", sec: true }),
				kv([["Reply", c.reply.body], ["Received", c.reply.received]], { title: "Supplier reply", sec: true }),
				sg("Result", ["Meets", "Does not meet", "Needs review"], -1, { name: "result" }), reason,
				{ k: "links", links: [{ label: "The reply changes the offer", action: "set", args: { name: "disposition", value: "Excluded change" } }] }],
			pri: record("Considered", ["result", "reason"]), sec: [end] };
	}
	if (decision === "verification-outcome") {
		const ver = work.verification;
		const r = experienceRequirement(ctx);
		return { ...base, guidance: guidance(data, { headline: "Record how verification affects the evaluation." }),
			blocks: [attendanceTable(work.session, data, { membersOnly: true }),
				tb(["Participant", "Signature"], ver.signatures.map((s) => [s.name, s.signed ? `Signed ${s.signed.split(", ")[1] || s.signed}` : "Awaiting signature"]), { title: "Verification report 1", sec: true }),
				...ver.observations.map((o) => at(o.findings)), sg("Result", ["Meets", "Does not meet", "Needs review"], -1, { name: "result" }), fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" })],
			pri: cmd("Record conclusion", "record_verification_outcome", { values: { bid: r.bid, requirement_key: r.requirement_key }, fields: ["result", "reason"] }),
			sec: [nav("View verification report", "verification"), end] };
	}
	if (decision === "verification") {
		const members = (data.committee || {}).members || [];
		const chosen = members.filter((m) => form[`p_${m.user}`]);
		return { ...base, guidance: guidance(data, { headline: "Record the committee’s verification plan." }),
			blocks: [attendanceTable(work.session, data, { membersOnly: true }), comparisonTable(data, { title: "Refreshed comparison", sec: true }),
				fi("Scope", "", { req: true, name: "scope" }), fi("Basis", "", { req: true, name: "basis" }),
				{ k: "p", t: "Participants", strong: false, muted: true },
				...members.map((m) => cb(m.name, false, { name: `p_${m.user}` })),
				{ k: "p", t: "Selected from the current eligible committee.", muted: true },
				fi("Lead", "", { select: true, req: true, name: "lead", options: [{ value: "", label: "Choose the lead" }].concat((chosen.length ? chosen : members).map((m) => ({ value: m.user, label: m.name }))) }),
				switcher("verification")],
			pri: cmd("Record verification plan", "record_verification_plan", { values: { compose: "participants" }, fields: ["scope", "basis", "lead"] }), sec: [end] };
	}
	if (decision === "basis") {
		// EVL-CHG-001 v0.4 §11.1 (16 Jun 09:05:30): the committee records why no
		// additional due diligence is needed, as a conclusion of the whole case.
		return { ...base, guidance: guidance(data, { headline: "Record the committee’s conclusion." }),
			blocks: [att, f(["Subject", "Due diligence"]), fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" }), switcher("basis")],
			pri: cmd("Record conclusion", "record_case_conclusion", { values: { kind: "Due diligence basis" }, fields: ["reason"] }), sec: [end] };
	}
	if (decision === "clarification") {
		const note = ((work.notes || []).slice(-1)[0]) || null;
		const blocks = [att, subject.block];
		if (note) blocks.push(kv([["Discussion note", note.note], ["Reason", note.reason || ""]], { title: "Proposed conclusion", sec: true }));
		blocks.push(fi("Question", "", { area: true, req: true, rows: 2, name: "question" }), fi("Reply deadline", "", { req: true, name: "reply_deadline", type: "datetime-local" }),
			fi("Scope", "Explain the submitted evidence. Do not change your offer or add a new service arrangement.", { area: true, req: true, rows: 2, name: "reply_scope" }), switcher("clarification"));
		return { ...base, guidance: guidance(data, { headline: "Authorise the agreed written clarification." }), blocks,
			pri: cmd("Authorise clarification", "authorise_clarification", { values: { bid: item.evaluation_bid, requirement_key: item.requirement_key }, fields: ["question", "reply_deadline", "reply_scope"] }), sec: [end] };
	}
	// D05-CONCLUSION / D05-CONCLUSION-Q
	const blocks = [att, subject.block, evd, sg("Result", ["Meets", "Does not meet", "Needs review"], -1, { name: "result" })].filter(Boolean);
	if (form.result === "Needs review") blocks.push(f(["Outcome", "Qualified report"]));
	blocks.push(fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" }), switcher("conclusion"));
	return { ...base, guidance: guidance(data, { headline: "Record the committee’s conclusion." }), blocks,
		pri: cmd("Record conclusion", "record_conclusion", { values: { bid: item.evaluation_bid, requirement_key: item.requirement_key, compose: "qualified" }, fields: ["result", "reason"] }), sec: [end] };
}

function experienceRequirement(ctx) {
	const bid = ctx.bid || { requirements: [] };
	const r = bid.requirements.find((x) => /experience/i.test(x.label)) || bid.requirements.find((x) => x.result === "Needs review") || bid.requirements[0] || {};
	return { bid: bid.bid, requirement_key: r.requirement_key };
}

export function disagreeDialog(ctx) {
	return {
		t: "Record disagreement",
		blocks: [fi("Your disagreement", "", { area: true, req: true, rows: 3, name: "statement" })],
		pri: cmd("Save disagreement", "record_disagreement", { values: { conclusion: (ctx.dialogArgs || {}).conclusion || "" }, fields: ["statement"], close: true }),
	};
}
