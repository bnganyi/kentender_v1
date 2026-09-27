// BDS-CHG-001 v0.8 §10.13 fixture payloads for BDS-DES-12 as the server sends
// them (`get_submit_page`), and the structural-fidelity variants at both
// frames. The confirmation-dialog variant compares the page beneath the
// dialog (ConfirmSubmitDialog.vue).
import SubmitScreen from "./SubmitScreen.vue";
import { workspace } from "./workspace.fixtures.js";

const REF = "TND-MOH-2027-033";
const BID = "BID-MOH-2027-033-001";
const BASE = `/tenders/${REF}/bid`;
const DEADLINE = "12 Jun 2027, 11:00 EAT";
const SUPPORT = { label: "Supplier support", href: "mailto:supplier.support@kentender.example" };
const fix = (fix_id, label, primary = true, target = null) => ({ fix_id, label, responsibility: "Authorised Signatory", person: "", kind: fix_id === "contact_support" ? "route" : "command", target, primary });

function guidance(variant) {
	const signatory = workspace("SIGNATORY");
	const base = signatory.next_step;
	switch (variant) {
		case "PENDING":
			return { next_step: { ...base, kind: "waiting", label: "Waiting on someone", headline: "Technical operator Daniel Otieno is checking the same submission attempt.", sentence: "No new Submit or retry action." }, journey: workspace("OUTAGE").journey };
		case "CERTIFICATE": {
			const check = fix("check_certificate", "Check certificate");
			return {
				next_step: { ...base, kind: "your_turn_blocked", label: "Your turn, blocked", headline: "Obtain a valid digital signature certificate from an approved licensed certifying agency before submitting.", sentence: "Your bid remains saved and has not been submitted. Supplier support can explain the process but cannot waive it.", fixes: [check], blockers: [{ reason_code: "BDS_SIGNATORY_CERTIFICATE_REQUIRED", message: "", headline: "", figures: {}, facts: [], fixes: [check] }] },
				journey: signatory.journey,
			};
		}
		case "SIGNATURE":
			return { next_step: { ...base, kind: "waiting", label: "Waiting on someone", headline: "Technical operator Daniel Otieno is restoring digital signing.", sentence: "" }, journey: workspace("OUTAGE").journey };
		case "SERVICE":
			return { next_step: { ...workspace("OUTAGE").next_step, sentence: "" }, journey: workspace("OUTAGE").journey };
		case "REJECTED": {
			const fixes = [fix("submit_bid", "Try confirmation again"), fix("contact_support", "Contact support", false)];
			return {
				next_step: { ...base, kind: "your_turn_blocked", label: "Your turn, blocked", headline: "The tender box rejected this attempt; no bid was submitted.", sentence: "Reference TBX-REJECT-033-01. Your bid remains saved and was not submitted.", fixes, blockers: [{ reason_code: "BDS_CUSTODY_REJECTED", message: "", headline: "", figures: {}, facts: [], fixes }] },
				journey: signatory.journey,
			};
		}
		case "CFG":
			return { next_step: { ...workspace("CFG-READY").next_step, sentence: "Saved work and receipts remain available while required supplier portal information is restored." }, journey: workspace("CFG-READY").journey };
		case "GATE":
			return { next_step: { ...workspace("GATE").next_step, sentence: "" }, journey: workspace("GATE").journey };
		default:
			return { next_step: base, journey: signatory.journey };
	}
}

const NOTICES = {
	SIGNATURE: { tone: "critical", title: "Digital signing is temporarily unavailable", text: "Your bid remains saved and has not been submitted. The signing service is being restored.", links: [SUPPORT] },
	SERVICE: { tone: "critical", title: "Electronic submission is temporarily unavailable", text: "Your bid remains saved and no receipt exists.", links: [{ label: "View status", href: `${BASE}/status` }, SUPPORT] },
	GATE: { tone: "critical", title: "Electronic bid submission is not available yet", text: "Your bid remains saved and has not been submitted.", links: [SUPPORT] },
};
const CONFIRM = { kind: "confirm", confirmation: "I confirm that the information, declarations and evidence in this bid are correct and that I am authorised to submit it for Afya Digital Supplies Limited.", submit_label: "Submit bid", cancel_href: `${BASE}/review` };

/** One `get_submit_page` read for a board variant ("", PENDING, CERTIFICATE, SIGNATURE, SERVICE, REJECTED, CFG, GATE). */
export function submitPage(variant = "") {
	const decision = variant === "" ? CONFIRM : variant === "PENDING" ? { kind: "pending", text: "We are checking this submission attempt. You may leave and return through View status. Do not submit again while this attempt is pending.", status_href: `${BASE}/status`, submit_label: "Submitting bid…" } : null;
	const certificate = variant === "CERTIFICATE" ? { label: "Not available", tone: "critical" } : { label: "Ready", tone: "live" };
	return {
		bid: { reference: BID, tender_reference: REF, record_version: 52 },
		page: { title: "Submit bid", description: "Digitally sign and place this bid in the electronic tender box.", back_href: `${BASE}/review`, back_label: "Back to review" },
		...guidance(variant),
		consequence: decision ? { tone: "warning", text: `After submission, this Version cannot be edited. You may prepare a replacement or withdraw it before ${DEADLINE}. The bid will not be opened or evaluated now.` } : null,
		notice: NOTICES[variant] || null,
		action: variant === "GATE" ? { label: "Back to bid", href: BASE, tone: "secondary" } : variant === "CFG" ? { label: "Continue saved bid", href: BASE, tone: "secondary" } : null,
		meta: [{ label: "Current server time", value: "10 Jun 2027, 14:30 EAT" }, { label: "Submission deadline", value: DEADLINE }],
		summary: [
			{ label: "Tender", value: `Supply and delivery of business laptops · ${REF}` }, { label: "Bidder", value: "Afya Digital Supplies Limited" }, { label: "Bid", value: `${BID} · Draft Version 7` },
			{ label: "Bid total", value: "KES 46,400,000.00", strong: true }, { label: "Current deadline", value: DEADLINE }, { label: "Addendum acknowledged", value: "ADD-MOH-2027-033-001 · 1 Jun 2027, 12:10 EAT" },
			{ label: "Tender-security physical receipt", value: "MOH-SEC-2027-033-017 · 10 Jun 2027, 10:00 EAT" },
		],
		signatory: [
			{ label: "Signatory", value: "Mary Wanjiku" }, { label: "Job title", value: "Managing Director" }, { label: "Authority evidence", value: "Available" },
			{ label: "Digital certificate", value: certificate.label, status: certificate },
		],
		decision,
		dialog: {
			title: "Submit this bid?",
			text: "KenTender will apply your digital signature and submit this exact Version to the electronic tender box. Wait for the submission receipt to confirm acceptance. If confirmation takes longer, you can return through View status; do not submit again while the same attempt is being checked.",
			facts: [{ label: "Tender", value: REF }, { label: "Bidder", value: "Afya Digital Supplies Limited" }, { label: "Bid total", value: "KES 46,400,000.00" }, { label: "Deadline", value: DEADLINE }],
		},
		support_href: SUPPORT.href,
		retry: variant === "REJECTED" ? CONFIRM : null,
	};
}

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	[
		["BDS-DES-12", ""], ["BDS-DES-12 confirmation dialog", ""], ["BDS-DES-12-PENDING", "PENDING"], ["BDS-DES-12-CERTIFICATE", "CERTIFICATE"], ["BDS-DES-12-SIGNATURE", "SIGNATURE"],
		["BDS-DES-12-SERVICE", "SERVICE"], ["BDS-DES-12-REJECTED", "REJECTED"], ["BDS-DES-12-CFG", "CFG"], ["BDS-DES-12-GATE", "GATE"],
	].map(([variant, key]) => ({ name: "SubmitScreen", variant, frame, component: SubmitScreen, props: { initial: submitPage(key), reference: REF }, path: `${BASE}/submit` })),
);
