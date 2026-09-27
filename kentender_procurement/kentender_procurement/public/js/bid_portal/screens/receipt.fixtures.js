// BDS-CHG-001 v0.8 §10.14–10.15 fixture payloads for BDS-DES-13 and the
// receipt BDS-DES-14-REPLACED reuses, as the server sends them
// (`get_receipt_page`), and the structural-fidelity variants at both frames.
// The withdrawal-dialog variant compares the receipt page beneath the dialog
// (WithdrawDialog.vue).
import ReceiptScreen from "./ReceiptScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const BID = "BID-MOH-2027-033-001";
const API = "/api/method/kentender_procurement.bid_submission.api.";
const answer = (kind, label, headline, sentence = "") => ({ ...workspace("SIGNATORY").next_step, kind, label, headline, sentence, fixes: [], blockers: [] });

/** One `get_receipt_page` read for a board variant ("", REPRESENTATIVE, CLOSED, REPLACED, WITHDRAW). */
export function receiptPage(variant = "") {
	const tender = variant === "WITHDRAW" ? "TND-MOH-2027-041" : REF;
	const bid = variant === "WITHDRAW" ? "BID-MOH-2027-041-001" : BID;
	const receipt = variant === "REPLACED" ? "RCPT-MOH-2027-033-002" : variant === "WITHDRAW" ? "RCPT-MOH-2027-041-001" : "RCPT-MOH-2027-033-001";
	const signatory = ["", "WITHDRAW"].includes(variant);
	const actions = [
		...(signatory ? [{ key: "prepare_replacement", label: "Prepare replacement", href: `/tenders/${tender}/bid/replace`, tone: "secondary" }, { key: "withdraw_bid", label: "Withdraw bid", href: "", tone: "danger" }] : []),
		{ key: "print", label: "Print receipt", href: `${API}download_bid_receipt?receipt_reference=${receipt}&inline=1`, tone: "primary" },
	];
	const next_step = {
		"": answer("your_turn", "Your turn", "You may prepare a replacement or withdraw before 12 Jun 2027, 11:00 EAT. Version 1 remains submitted.", "These are options, not assigned overdue work."),
		WITHDRAW: answer("your_turn", "Your turn", "You may prepare a replacement or withdraw before 12 Jun 2027, 11:00 EAT. Version 1 remains submitted.", "These are options, not assigned overdue work."),
		REPRESENTATIVE: answer("done", "Done", "Bid Version 1 was accepted on 10 Jun 2027, 14:32:01 EAT."),
		CLOSED: answer("done", "Done", "Bid Version 1 remains submitted; submission changes closed at 12 Jun 2027, 11:00 EAT."),
		REPLACED: answer("done", "Done", "Bid Version 2 was accepted on 11 Jun 2027, 09:15:04 EAT."),
	}[variant];
	return {
		kind: "receipt",
		bid: { reference: bid, tender_reference: tender, record_version: 60 },
		page: {
			title: variant === "REPLACED" ? "Replacement bid submitted" : "Bid submitted",
			description: variant === "REPLACED" ? "Your replacement bid was accepted into the electronic tender box." : "Your bid was accepted into the electronic tender box.",
			badge: { label: "Submitted", tone: "live" },
		},
		actions, next_step, journey: workspace("SIGNATORY").journey,
		receipt: [
			{ label: "Receipt reference", value: receipt, strong: true }, { label: "Tender", value: tender }, { label: "Bidder", value: "Afya Digital Supplies Limited" }, { label: "Bid", value: bid },
			{ label: "Submitted bid Version", value: variant === "REPLACED" ? "2" : "1" }, { label: "Submitted by", value: "Mary Wanjiku" },
			{ label: "Received by tender-box service", value: "10 Jun 2027, 14:31:58 EAT" }, { label: "Accepted into tender box", value: "10 Jun 2027, 14:32:01 EAT" },
			{ label: "Status", value: "Submitted", status: { label: "Submitted", tone: "live" } },
		],
		lineage: variant === "REPLACED" ? { status: { label: "Version 1 superseded", tone: "pending" }, link: { label: "View Version 1 receipt · RCPT-MOH-2027-033-001", href: `/tenders/${REF}/bid/receipt/RCPT-MOH-2027-033-001` } } : null,
		summary: [
			{ label: "Bid total", value: "KES 46,400,000.00", strong: true }, { label: "Offered item", value: "ApexBook Pro 14" }, { label: "Quantity", value: "250 Each" },
			{ label: "Delivery date", value: "15 Sep 2027" }, { label: "Current deadline", value: "12 Jun 2027, 11:00 EAT" },
		],
		notice: "This receipt confirms submission only. It is not an opening, evaluation or award result.",
		sentence: signatory ? "The current submitted bid remains valid until a replacement is accepted or a withdrawal is acknowledged." : variant === "CLOSED" ? "Submission changes closed on 12 Jun 2027, 11:00 EAT." : "",
		withdrawal: signatory ? { receipt_reference: receipt, deadline: "12 Jun 2027, 11:00 EAT" } : null,
		footer: { back_href: "/my-bids", download_href: `${API}download_bid_receipt?receipt_reference=${receipt}` },
	};
}

/** The `get_receipt_page` read for a withdrawal acknowledgement (BDS-DES-14-WITHDRAWN, the isolated TND-MOH-2027-041 facts). */
export function acknowledgementPage({ signatory = true } = {}) {
	const tender = "TND-MOH-2027-041";
	return {
		kind: "acknowledgement",
		bid: { reference: "BID-MOH-2027-041-001", tender_reference: tender, record_version: 70 },
		page: { title: "Bid withdrawn", description: "Your withdrawal was acknowledged. The submitted history is retained.", badge: { label: "Withdrawn", tone: "critical" } },
		next_step: signatory
			? answer("your_turn", "Your turn", "You may start a new bid before the deadline. This bid was withdrawn; no bid is currently submitted.", "This is an available option, not overdue work.")
			: answer("done", "Done", "This bid was withdrawn; no bid is currently submitted."),
		journey: workspace("SIGNATORY").journey,
		acknowledgement: [
			{ label: "Acknowledgement reference", value: "WD-MOH-2027-041-001", strong: true }, { label: "Tender", value: `Supply and delivery of network switches · ${tender}` },
			{ label: "Bidder", value: "Afya Digital Supplies Limited" }, { label: "Bid", value: "BID-MOH-2027-041-001" }, { label: "Withdrawn by", value: "Mary Wanjiku" },
			{ label: "Withdrawn at", value: "10 Jun 2027, 15:00:00 EAT" }, { label: "Status", value: "Withdrawn", status: { label: "Withdrawn", tone: "critical" } },
		],
		footer: { back_href: "/my-bids", download_href: `${API}download_withdrawal_acknowledgement?acknowledgement_reference=WD-MOH-2027-041-001`, start: signatory ? { label: "Start replacement", next_href: `/tenders/${tender}/bid` } : null },
	};
}

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	[["BDS-DES-13", ""], ["BDS-DES-13-REPRESENTATIVE", "REPRESENTATIVE"], ["BDS-DES-13-CLOSED", "CLOSED"], ["BDS-DES-14-REPLACED", "REPLACED"], ["BDS-DES-14 withdrawal dialog", "WITHDRAW"]].map(([variant, key]) => {
		const initial = receiptPage(key);
		return { name: "ReceiptScreen", variant, frame, component: ReceiptScreen, props: { initial, reference: initial.bid.tender_reference, receipt: initial.receipt[0].value }, path: `/tenders/${initial.bid.tender_reference}/bid/receipt/${initial.receipt[0].value}` };
	}).concat([{ name: "ReceiptScreen", variant: "BDS-DES-14-WITHDRAWN", frame, component: ReceiptScreen, props: { initial: acknowledgementPage(), reference: "TND-MOH-2027-041", receipt: "WD-MOH-2027-041-001" }, path: "/tenders/TND-MOH-2027-041/bid/receipt/WD-MOH-2027-041-001" }]),
);
