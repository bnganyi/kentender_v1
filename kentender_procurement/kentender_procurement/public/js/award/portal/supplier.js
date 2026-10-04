// The supplier's award notice in the portal (AWD-CHG-001 v0.4 §9, §10.2 D04,
// §10.3 V13, V14, V22; dialogs X01, X02, X11) from GetSupplierAwardNotice:
// their own result, notice, response and explanation request only — no
// internal tracker, no other recipient's letter.
import { btn } from "../board/model.js";

export function supplierBoard(n, { viewing = false } = {}) {
	const hdr = { title: n.tender_title, desc: [n.tender_reference, n.procuring_entity].filter(Boolean).join(" · ") };
	const base = { hdr, kicker: "Award notice", next: { k: n.next_step.kind, h: n.next_step.headline, s: n.next_step.sentence } };
	if (viewing) {
		return { ...base, screen: "supplier-letter", next: null, sec: [{ t: "Award notice", p: [n.statement, n.reason].filter(Boolean), f: noticeFacts(n) }],
			act: [btn("Back", "back-to-notice")], place: "row" };
	}
	if (n.result === "Unsuccessful") {
		return { ...base, screen: "supplier-unsuccessful", next: { k: "done", l: "Result", h: n.next_step.headline },
			sec: [{ t: "Award result", f: [["Your submitted and evaluated amount", n.own_amount], ["Successful supplier", n.successful_supplier], ["Evaluated and award amount", n.award_amount]],
				d: [["Reason", n.reason]] }], act: [btn("View notice", "view-notice"), btn("Request explanation", "dialog", { name: "request-explanation" })], place: "row" };
	}
	const late = (n.responses || []).find((r) => r.late);
	if (late) {
		return { ...base, screen: "supplier-late", sec: [{ t: "Your response", f: [["Received", late.received_at], ["Reply deadline", n.reply_deadline]] }],
			act: [btn("View response", "view-notice"), btn("View notice", "view-notice")], place: "row" };
	}
	const section = { t: "Award notice", f: noticeFacts(n), note: n.not_a_contract };
	if (n.can_respond) {
		return { ...base, screen: "supplier-notice", sec: [section], place: "decision",
			act: [btn("View notice", "view-notice"), btn("Request explanation", "dialog", { name: "request-explanation" }), btn("Decline award", "dialog", { name: "decline" }),
				btn("*Accept award", "dialog", { name: "accept", wording: n.accept_wording })] };
	}
	return { ...base, screen: n.is_signatory ? "supplier-responded" : "supplier-representative", sec: [section],
		act: [btn("View notice", "view-notice"), btn("Request explanation", "dialog", { name: "request-explanation" })], place: "row" };
}

function noticeFacts(n) {
	return [["Tender", n.tender_reference], ["Supplier", n.organisation_name], ["Amount", n.amount || n.award_amount], ["Notice", n.notice_label]]
		.concat(n.reply_deadline ? [["Reply by", n.reply_deadline]] : []);
}

export function noticesBoard(list) {
	return { hdr: { title: "Award notices" }, screen: "supplier-list", sec: [{ t: "Award notice", ...(list.length ? { tbl: { h: ["Tender", "Notice", "Result"], a: "Open",
		r: list.map((x) => [x.tender_reference, x.label, x.result]), actions: list.map((x) => ({ action: "open-notice", args: { notice: x.notice } })) } }
		: { empty: "You have no award notices." }) }] };
}
