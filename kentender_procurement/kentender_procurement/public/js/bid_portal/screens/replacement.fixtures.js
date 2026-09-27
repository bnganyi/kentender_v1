// BDS-CHG-001 v0.8 §10.15 fixture payloads for BDS-DES-14 (Prepare
// replacement bid) as the server sends them (`get_replacement_page`), and the
// structural-fidelity variant at both frames.
import ReplacementScreen from "./ReplacementScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const BASE = `/tenders/${REF}/bid`;

/** One `get_replacement_page` read ("" — Mary may create; OPEN — a replacement Draft is open). */
export function replacementPage(variant = "") {
	const open = variant === "OPEN";
	return {
		bid: { reference: "BID-MOH-2027-033-001", tender_reference: REF, record_version: 61 },
		page: { title: "Prepare replacement bid", description: "Create a new Draft while the submitted bid remains valid.", badge: { label: "Version 1 submitted", tone: "live" } },
		next_step: { ...workspace("SIGNATORY").next_step, headline: "You may prepare a replacement or withdraw before 12 Jun 2027, 11:00 EAT. Version 1 remains submitted.", sentence: "These are options, not assigned overdue work.", fixes: [] },
		journey: workspace("SIGNATORY").journey,
		notice: { text: "Receipt RCPT-MOH-2027-033-001 remains current until the replacement is accepted.", link: { label: "View receipt", href: `${BASE}/receipt/RCPT-MOH-2027-033-001` } },
		facts: [
			{ label: "Current submitted bid Version", value: "1" }, { label: "Submitted", value: "10 Jun 2027, 14:32 EAT" }, { label: "Deadline", value: "12 Jun 2027, 11:00 EAT" },
			{ label: "Current definition includes", value: "ADD-MOH-2027-033-001" },
		],
		text: open ? "Your replacement Draft is open. Version 1 remains submitted until the replacement is accepted." : "The new Draft copies your organisation's working responses and current published requirements. Review every changed value before submitting.",
		decision: open ? null : { cancel_href: `${BASE}/receipt/RCPT-MOH-2027-033-001`, create_label: "Create replacement Draft", next_href: BASE },
		continue: open ? { label: "Continue replacement Draft", href: BASE } : null,
	};
}

export const SCREENS = ["desktop", "narrow"].map((frame) => ({ name: "ReplacementScreen", variant: "BDS-DES-14", frame, component: ReplacementScreen, props: { initial: replacementPage(), reference: REF }, path: `${BASE}/replace` }));
