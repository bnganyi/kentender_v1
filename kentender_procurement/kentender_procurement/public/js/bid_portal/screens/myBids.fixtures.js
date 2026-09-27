// BDS-CHG-001 v0.8 §10.6 and §10.20 fixture payloads as the server sends them
// (`get_my_bids`, `get_receipt_history`), and the structural-fidelity variants
// for boards BDS-DES-05 and BDS-DES-17 at both frames.
import MyBidsScreen from "./MyBidsScreen.vue";
import ReceiptHistoryScreen from "./ReceiptHistoryScreen.vue";

const OPTIONS = { status: ["", "Draft", "Needs attention", "Ready to submit", "Submitted", "Withdrawn", "Closed without submission"].map((v) => ({ value: v, label: v || "All statuses" })) };
const LAPTOPS = { tender_reference: "TND-MOH-2027-033", tender_title: "Supply and delivery of business laptops", deadline_label: "12 Jun 2027, 11:00 EAT" };
const SWITCHES = { tender_reference: "TND-MOH-2027-041", tender_title: "Supply and delivery of network switches", deadline_label: "12 Jun 2027, 11:00 EAT" };

const ROWS = {
	"": { ...LAPTOPS, bid_reference: "BID-MOH-2027-033-001", status: "Ready to submit", status_label: "Ready to submit", status_tone: "live", version_label: "Draft Version 7", updated_label: "10 Jun 2027, 13:50 EAT", actions: [{ label: "Review bid", href: "/tenders/TND-MOH-2027-033/bid/review" }] },
	SUBMITTED: { ...LAPTOPS, bid_reference: "BID-MOH-2027-033-001", status: "Submitted", status_label: "Submitted", status_tone: "live", version_label: "Submitted bid Version 1", updated_label: "10 Jun 2027, 14:32 EAT", actions: [{ label: "View receipt", href: "/tenders/TND-MOH-2027-033/bid/receipt/RCPT-MOH-2027-033-001" }] },
	WITHDRAWN: {
		...SWITCHES, bid_reference: "BID-MOH-2027-041-001", status: "Withdrawn", status_label: "Withdrawn", status_tone: "critical", version_label: "", updated_label: "10 Jun 2027, 15:00 EAT",
		actions: [{ label: "View acknowledgement", href: "/tenders/TND-MOH-2027-041/bid/receipt/WD-MOH-2027-041-001" }, { label: "Start replacement", href: "/tenders/TND-MOH-2027-041/bid", command: "prepare_replacement", record_version: 9 }],
	},
};

/** One `get_my_bids` read for a board variant ("", SUBMITTED, WITHDRAWN, EMPTY). */
export function myBids(variant = "") {
	const rows = variant === "EMPTY" ? [] : [{ ...ROWS[variant] }];
	return { rows, count_text: rows.length === 1 ? "1 bid" : `${rows.length} bids`, empty_text: "No bids yet. Find a Tender to start your first bid.", options: OPTIONS, applied: { search: "", status: "" }, work: [] };
}

const RECEIPTS = [
	{ ...LAPTOPS, document: "RCPT-MOH-2027-033-001", event: "Submitted", event_tone: "live", at_label: "10 Jun 2027, 14:32:01", href: "/tenders/TND-MOH-2027-033/bid/receipt/RCPT-MOH-2027-033-001" },
	{ ...SWITCHES, document: "WD-MOH-2027-041-001", event: "Withdrawn", event_tone: "critical", at_label: "10 Jun 2027, 15:00:00", href: "/tenders/TND-MOH-2027-041/bid/receipt/WD-MOH-2027-041-001" },
];

/** One `get_receipt_history` read for a board variant ("", EMPTY, SUSPENDED). */
export function receipts(variant = "") {
	const rows = variant === "EMPTY" ? [] : RECEIPTS.map((r) => ({ ...r }));
	return {
		outcome: "OK", rows, count_text: rows.length === 1 ? "1 record" : `${rows.length} records`, empty_text: "No submission or withdrawal receipts for this organisation.",
		suspended: variant === "SUSPENDED", suspended_text: variant === "SUSPENDED" ? "This supplier account is suspended. You can read and download existing receipts; no bid can be prepared, submitted, replaced or withdrawn." : "",
	};
}

export const SCREENS = ["desktop", "narrow"].flatMap((frame) => [
	...["", "-SUBMITTED", "-WITHDRAWN", "-EMPTY"].map((suffix) => ({ name: "MyBidsScreen", variant: `BDS-DES-05${suffix}`, frame, component: MyBidsScreen, props: { initial: myBids(suffix.slice(1)) }, path: "/my-bids" })),
	...["", "-EMPTY", "-SUSPENDED"].map((suffix) => ({ name: "ReceiptHistoryScreen", variant: `BDS-DES-17${suffix}`, frame, component: ReceiptHistoryScreen, props: { initial: receipts(suffix.slice(1)) }, path: "/account/receipts" })),
]);
