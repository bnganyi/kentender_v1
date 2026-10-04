// BDS-CHG-001 v0.8 §10.12 fixture payloads for BDS-DES-11 as the server sends
// them (`get_bid_task` for the review task), and the structural-fidelity
// variants at both frames.
import ReviewTaskScreen from "./ReviewTaskScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const BID = "BID-MOH-2027-033-001";
const BASE = `/tenders/${REF}/bid`;
const SUBMIT = { label: "Submit bid", href: `${BASE}/submit` };
const TASKS = [["documents", "Tender documents, clarifications and addenda"], ["company", "Company, declarations and tender security"], ["requirements", "Requirements and supporting evidence"], ["price", "Price"], ["review", "Review and submit"]];
const TONES = { Complete: "live", "Needs attention": "attention" };

function taskRows(states, issues = {}) {
	return TASKS.map(([key, label], i) => ({ key, label, status: states[i], tone: TONES[states[i]] || "draft", issues: issues[key] || [], href: key === "review" ? "" : `${BASE}/${key}` }));
}
const facts = (pairs) => pairs.map(([label, value, strong]) => ({ label, value, ...(strong ? { strong: true } : {}) }));

/** One review-task read for a board variant ("", EVIDENCE, ADDENDUM, REPRESENTATIVE, CFG-PREP, CFG-READY). */
export function reviewTask(variant = "") {
	const ready = ["", "REPRESENTATIVE", "CFG-READY"].includes(variant);
	const guided = workspace({ "": "SIGNATORY", REPRESENTATIVE: "", ADDENDUM: "ADDENDUM", "CFG-PREP": "CFG-PREP", "CFG-READY": "CFG-READY", EVIDENCE: "SIGNATORY" }[variant]);
	let next_step = { ...guided.next_step };
	if (variant === "EVIDENCE") {
		const fix = { fix_id: "fix_item:requirements", label: "Fix item", responsibility: "Supplier user", person: "", kind: "route", target: { task: "requirements", handle: "h-datasheet" }, primary: true };
		next_step = { ...next_step, kind: "your_turn_blocked", label: "Your turn, blocked", headline: "Replace the rejected product datasheet before submitting.", fixes: [fix], blockers: [{ reason_code: "BDS_EVIDENCE_REJECTED", message: "", headline: "", figures: {}, facts: [], fixes: [fix] }] };
	}
	if (variant === "CFG-PREP") next_step = { ...next_step, fixes: [] };
	const states = {
		EVIDENCE: ["Complete", "Complete", "Needs attention", "Complete", "Not started"],
		ADDENDUM: ["Needs attention", "Complete", "Needs attention", "Complete", "Not started"],
		"CFG-PREP": ["Complete", "Complete", "Complete", "In progress", "Not started"],
	}[variant] || ["Complete", "Complete", "Complete", "Complete", "Complete"];
	const issues = {
		EVIDENCE: { requirements: [{ label: "Replace the rejected product datasheet", href: `${BASE}/requirements?item=g-datasheet` }] },
		ADDENDUM: { requirements: [{ label: "Confirm the current delivery location", href: `${BASE}/requirements` }] },
	}[variant] || {};
	const action = { "": { ...SUBMIT, tone: "primary" }, "CFG-PREP": { label: "Continue saved bid", href: `${BASE}/price`, tone: "primary" }, "CFG-READY": { label: "Continue saved bid", href: BASE, tone: "secondary" } }[variant] || null;
	return {
		bid: { reference: BID, tender_reference: REF, status: ready ? "Ready to submit" : "Needs attention", record_version: 52 },
		page: { title: "Review bid", description: "Check the complete bid before submitting it to the electronic tender box.", back_href: BASE, action },
		next_step, journey: guided.journey,
		result: ready ? { tone: "live", text: "All required bid information is complete." } : null,
		availability_notice: variant === "CFG-PREP" ? { tone: "warning", title: "Submission is unavailable", text: "Supplier portal information is being restored. Your saved bid can still be reviewed and saved.", links: [] } : null,
		security_notice: { tone: "live", title: "", text: "Physical tender-security original recorded as received on 10 Jun 2027, 10:00 EAT." },
		summary: facts([
			["Tender", `Supply and delivery of business laptops · ${REF}`], ["Bidder", "Afya Digital Supplies Limited · Single organisation"], ["Bid", `${BID} · Draft Version 7`],
			["Current deadline", "12 Jun 2027, 11:00 EAT"], ["Signatory", "Mary Wanjiku · Managing Director"], ["Bid total", "KES 46,400,000.00", true],
		]),
		task_rows: taskRows(states, issues),
		offering: facts([["Offered model", "ApexBook Pro 14"], ["Quantity", "250 Each"], ["Delivery", "15 Sep 2027"], ["Warranty", "36 months"], ["Support response", "4 hours"]]),
		declarations: facts([["Declarations", "5 confirmed · 2 complete"], ["Evidence items", variant === "EVIDENCE" ? "9 accepted · 1 rejected" : "10 accepted"], ["Tender security reference", "KCB/TG/2027/8841"], ["Physical receipt", "MOH-SEC-2027-033-017"]]),
		price_summary: facts([["Subtotal excluding tax", "KES 40,000,000.00"], ["Tax", "KES 6,400,000.00"], ["Bid total", "KES 46,400,000.00", true]]),
		footer: { back_href: BASE, submit: variant === "" ? SUBMIT : null },
	};
}

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	[
		["BDS-DES-11", ""], ["BDS-DES-11-EVIDENCE-ATTENTION", "EVIDENCE"], ["BDS-DES-11-ADDENDUM-ATTENTION", "ADDENDUM"], ["BDS-DES-11-REPRESENTATIVE", "REPRESENTATIVE"],
		["BDS-DES-11-CFG · in preparation", "CFG-PREP"], ["BDS-DES-11-CFG · ready", "CFG-READY"],
	].map(([variant, key]) => ({ name: "ReviewTaskScreen", variant, frame, component: ReviewTaskScreen, props: { initial: reviewTask(key), reference: REF }, path: `${BASE}/review` })),
);
