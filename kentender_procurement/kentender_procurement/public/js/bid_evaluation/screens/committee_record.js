// The committee record (EVL-CHG-001 v0.4 §9.6, §9.12; boards D05-RECORD,
// D05-RECORD-MEMBER, D05-RECORD-AUDITOR, D02-UNABLE's roster): the roster,
// sessions and attendance, correspondence, disagreement, and the
// appointment and declaration history. Read-only; a current member may
// record that they cannot continue.
import { ds, kv, p, tb } from "../board/model.js";
import { guidance, head, nav, recordTabs, rosterTable } from "./common.js";

const time = (when) => ((/(\d{2}:\d{2})/.exec(when || "") || [])[1] || "");
const day = (when) => String(when || "").split(",")[0];

export function committeeRecord(ctx) {
	const { data, record: rec } = ctx;
	if (!rec) return { ...head(data), ...recordTabs(1), blocks: [] };
	const blocks = [rosterTable(data)];
	const sessions = rec.sessions || [];
	if (sessions.length) {
		blocks.push(tb(["Session", "Time", "Subject", "Attendance"], sessions.map((s) => [day(s.start), `${time(s.start)}–${time(s.end)}`, s.subject,
			s.attendance.map((a, i) => `${a.name.split(" ")[0]} ${time(a.joined)}${i === 0 ? " (Start discussion)" : ""}`).join(" · ")]), { title: "Sessions", sec: true }));
	}
	(rec.clarifications || []).forEach((c) => {
		const rows = [["Question", c.question], ["Sent", c.sent], ["Reply deadline", c.deadline]];
		if (c.reply) rows.push(["Reply", `Received ${c.reply.received}${c.reply.timeliness === "Received late" ? " (late)" : ""}`]);
		if (c.status === "Closed") rows.push(["Committee outcome", `${c.closed} — ${c.disposition_reason}`]);
		if (c.status === "Withdrawn") rows.push(["Withdrawn", c.withdrawal_reason]);
		blocks.push(kv(rows, { title: "Clarification", sec: true }));
	});
	const said = rec.disagreements || [];
	if (said.length) blocks.push(tb(["Member", "Statement", "Recorded"], said.map((d) => [d.member, d.statement, d.at]), { title: "Disagreement", sec: true }));
	else blocks.push(p("No disagreement recorded", { strong: true }));
	const history = (rec.appointments || []).map((a) => `Committee ${a.kind === "Initial" ? "appointed" : a.kind.toLowerCase()} ${a.at} · ${a.reference}${a.reason ? ` — ${a.reason}` : ""}`);
	const sec = (data.committee || {}).secretary;
	if (sec) history.push(`Secretary ${sec.name} · ${sec.reference}`);
	const decl = (rec.declarations || []).map((d) => `${d.member} ${d.at} — ${d.choice === "Declare a conflict" ? "conflict declared" : "no conflict"}${d.status !== "Current" ? ` (${d.status.toLowerCase()})` : ""}`);
	if (decl.length) history.push(`Declarations: ${decl.join("; ")}`);
	blocks.push(ds("Appointment and declaration history", history));
	const v = data.viewer;
	const reader = v.auditor && !v.member && !v.secretary;
	const board = { ...head(data, { title: "Committee record" }), ...recordTabs(1), blocks };
	if (reader) return { ...board, notInvolved: " ", guidance: { answer: null, journey: data.tracker } };
	board.guidance = guidance(data);
	board.pri = ["Reviewing", "Signing", "Report sent"].includes(data.state) ? nav("View report", "report") : null;
	board.sec = [];
	if (v.secretary) board.sec.push(nav("Back to evaluation", []));
	if (v.member && !v.chair && ["Preparing", "Reviewing"].includes(data.state)) board.sec.push(nav("Record inability to serve", "unable"));
	return board;
}
