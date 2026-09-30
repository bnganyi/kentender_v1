// The supplier's reply to the evaluation committee (EVL-CHG-001 v0.4 §9.7,
// §9.11; boards D06-SUPPLIER, D06-RECEIVED, D06-LATE, D06-LATE-RECEIVED,
// D06-CLOSED, D06-FINAL-CLOSED, D06-FINAL-CLOSED-NR), drawn at 390 px in the
// supplier portal. Only the organisation's own request and reply: no finding,
// ranking or other bidder is ever read here.
import { f, fi, kv, lk } from "../board/model.js";

const qkv = (d) => kv([["Question", d.question], ["Scope", d.reply_scope], ["Sent", d.sent], ["Reply by", d.reply_deadline]], { title: "Committee question", sec: true });

export function supplierBoard(d, form) {
	const base = { size: "m", title: "Reply to clarification", desc: `${d.tender} · ${d.title}` };
	const back = { label: "Back to bid", action: "back-to-bid" };
	const reply = d.reply || {};
	const sent = reply.state === "Sent";
	const late = sent && /late/i.test(reply.timeliness || "");
	if (d.status === "Withdrawn") {
		// D06-CLOSED: withdrawn and replaced; the unsent draft stays private
		const blocks = [qkv(d), f(["Reason", `Request withdrawn: ${d.withdrawal_reason || "the question was replaced."}`])];
		if (reply.body && !sent) blocks.push(fi("Your unsent draft", reply.body, { area: true, rows: 3 }));
		if (d.replacement) {
			blocks.push(kv([["Question", d.replacement.question], ["Scope", d.reply_scope], ["Sent", d.replacement.sent], ["Reply by", d.replacement.reply_deadline]],
				{ title: "New question", sec: true }), { k: "links", links: [{ label: "View new question", action: "open-request", args: { clarification: d.replacement.clarification } }] });
		}
		return { ...base, nx: { k: "done", h: "This clarification has been withdrawn." }, blocks, sec: [back] };
	}
	if (d.status === "Closed") {
		// D06-FINAL-CLOSED / D06-FINAL-CLOSED-NR
		const blocks = [qkv(d)];
		if (sent) blocks.push(kv([["Your reply", reply.body], ["Reply received", late ? `Received late, ${reply.received}` : reply.received], ["Closed", d.closed]], { title: "Your reply", sec: true }));
		else {
			blocks.push(f(["Closed", d.closed]));
			if (reply.body) blocks.push(fi("Your unsent draft", reply.body, { area: true, rows: 3 }));
		}
		return { ...base, nx: { k: "done", h: "This clarification is closed." }, blocks, sec: [back] };
	}
	if (sent) {
		// D06-RECEIVED / D06-LATE-RECEIVED: no promise of acceptance
		return { ...base, nx: { k: "done", h: "Your reply has been received for committee review." },
			blocks: [qkv(d), kv([["Your reply", reply.body], [late ? "Received" : "Reply received", late ? `Received late, ${reply.received}` : reply.received]], { title: "Your reply", sec: true })],
			sec: [back] };
	}
	// D06-SUPPLIER / D06-LATE: the reply form; the submitted bid never changes
	const files = form.attachments || [];
	return {
		...base,
		nx: d.overdue ? { k: "turn", h: "The reply deadline has passed.", s: "You can send a late reply; the committee will decide whether it can be considered." }
			: { k: "turn", h: `Reply by ${d.reply_deadline}.` },
		blocks: [f(["Organisation", d.organisation_name || d.organisation]), qkv(d), fi("Your reply", "", { area: true, req: true, rows: 4, name: "body" }),
			fi("Supporting explanation", "", { file: true, name: "attachments", fileName: files.map((x) => x.filename).join(", "),
				help: "Attach only evidence explaining this question. Your submitted bid will not change." })],
		pri: { label: d.overdue ? "Send late reply" : "Send reply", action: "send-reply" },
		sec: [{ label: "Save draft", action: "save-draft" }, back],
	};
}

export { lk };
