// The committee's written clarification, internal side (EVL-CHG-001 v0.4
// §9.7, §9.11; boards D06-SEND, D06-DELIVERY, D06-WITHDRAW, D06-WITHDRAW-DLG).
// The authorised question and deadline are never editable here; the
// secretary sends it, retries a failed notice, or withdraws it for a
// replacement the chair authorised. The reply outcome is a committee
// decision recorded in the discussion (discussion.js).
import { f, fi, kv, n } from "../board/model.js";
import { cmd, dialog, guidance, nav } from "./common.js";

export function requestKv(c) {
	return kv([["Question", c.question], ["Scope", c.reply_scope], ["Reply deadline", c.deadline], ["Authorised", `${c.authorised_by_name}, ${c.authorised}`],
		["Recipient", c.bidder]], { title: "Clarification request", sec: true, testid: "evl-request" });
}

export function clarification(ctx) {
	const { data, id } = ctx;
	const c = ((data.work || {}).clarifications || []).find((x) => x.name === id);
	if (!c) return null;
	const v = data.viewer;
	const base = { title: c.status === "Authorised" ? "Send clarification" : "Clarification request", desc: `${data.tender} · ${data.title}` };
	const replacement = ((data.work || {}).clarifications || []).find((x) => x.replaces === c.name && x.status === "Authorised");
	if (v.secretary && c.status === "Authorised") {
		return { ...base, guidance: guidance(data, { headline: `Send the committee's question to ${c.bidder}.` }), blocks: [requestKv(c)],
			pri: cmd("Send clarification", "send_clarification", { values: { clarification: c.name } }), sec: [nav("Back to evaluation", [])] };
	}
	if (v.secretary && c.status === "Sent" && c.notice_state === "Delivery problem") {
		return { ...base, title: "Send clarification", guidance: guidance(data, { headline: "Retry the clarification notice." }),
			blocks: [n("warning", "The clarification notice could not be delivered.", "The question is available in the supplier’s bid workspace."), requestKv(c)],
			pri: cmd("Retry notice", "retry_clarification_notice", { values: { clarification: c.name } }), sec: [nav("Back to evaluation", [])] };
	}
	if (v.secretary && c.status === "Sent" && replacement) {
		return { ...base, guidance: guidance(data, { headline: "Withdraw the question authorised for replacement." }),
			blocks: [requestKv(c), f(["Chair's recorded reason", replacement.withdrawal_reason || replacement.replace_reason || ""])],
			pri: dialog("Withdraw clarification", "withdraw", { args: { name: "withdraw", clarification: c.name } }) };
	}
	const blocks = [requestKv(c)];
	if (c.sent) blocks.push(f(["Sent", c.sent], ["Notice", c.notice_state || "Pending"]));
	if (c.reply) blocks.push(kv([["Reply", c.reply.body], ["Received", c.reply.timeliness === "Late" ? `Received late, ${c.reply.received}` : c.reply.received]], { title: "Supplier reply", sec: true }));
	if (c.status === "Closed") blocks.push(f(["Outcome", `${c.disposition}${c.disposition_result ? ` · ${c.disposition_result}` : ""}`], ["Closed", c.closed]));
	if (c.status === "Withdrawn") blocks.push(f(["Withdrawn", c.withdrawal_reason || ""]));
	return { ...base, guidance: guidance(data), blocks, sec: [nav("Back to evaluation", [])] };
}

export function withdrawDialog(ctx) {
	return {
		t: "Withdraw this clarification?",
		blocks: [fi("Reason", "", { area: true, req: true, rows: 2, name: "withdraw_reason" })],
		pri: cmd("Withdraw clarification", "withdraw_clarification", { values: { clarification: (ctx.dialogArgs || {}).clarification || ctx.id }, fields: [["reason", "withdraw_reason"]], close: true }),
	};
}
