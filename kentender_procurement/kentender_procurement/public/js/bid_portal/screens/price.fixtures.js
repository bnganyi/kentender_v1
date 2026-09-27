// BDS-CHG-001 v0.8 §10.11 fixture payloads for BDS-DES-10 as the server sends
// them (`get_bid_task` for the price task), and the structural-fidelity
// variants at both frames.
import PriceTaskScreen from "./PriceTaskScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const MONEY = (handle, value) => ({ handle, kind: "money", label: "", help: "", editable: true, visible: true, required: true, value, shown_when: null, issue: null });

/** One price-task read for a board variant ("", INCOMPLETE). */
export function priceTask(variant = "") {
	const priced = variant !== "INCOMPLETE";
	const guided = workspace("IN-PROGRESS");
	return {
		bid: { reference: "BID-MOH-2027-033-001", tender_reference: REF, record_version: 40 },
		page: { title: "Price", description: "Enter your price for the published quantity. Totals are calculated automatically.", back_href: `/tenders/${REF}/bid` },
		badge: priced ? { label: "Complete", tone: "live" } : { label: "Needs attention", tone: "attention" },
		terms: "Currency KES · Fixed prices · Taxes shown separately.",
		lines: [{ line: "1", description: "Business laptops", quantity: "250", unit: "Each", unit_price: MONEY("p-unit", priced ? "160000.00" : null), tax: MONEY("p-tax", priced ? "6400000.00" : null), amount_before_tax: priced ? "KES 40,000,000.00" : "—" }],
		totals: priced ? { subtotal: "KES 40,000,000.00", tax: "KES 6,400,000.00", total: "KES 46,400,000.00", complete: true } : { subtotal: "—", tax: "—", total: "—", complete: false },
		note: "The Form of Tender uses this Bid total. You do not enter the total again.",
		footer: { save_label: "Save and continue", next_href: `/tenders/${REF}/bid/review` },
		next_step: { ...guided.next_step, headline: priced ? "Continue the review and submit task." : "Continue the price task.", sentence: "" }, journey: guided.journey,
	};
}

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	[["BDS-DES-10", ""], ["BDS-DES-10-INCOMPLETE", "INCOMPLETE"]].map(([variant, key]) => ({ name: "PriceTaskScreen", variant, frame, component: PriceTaskScreen, props: { initial: priceTask(key), reference: REF }, path: `/tenders/${REF}/bid/price` })),
);
