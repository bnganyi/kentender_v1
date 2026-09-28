// BDS-CHG-001 v0.8 §10.7 fixture payloads for BDS-DES-06 as the server sends
// them (`get_bid_workspace` with kentender_core's next-step and journey
// shapes), and the structural-fidelity variants at both frames.
import BidWorkspaceScreen from "./BidWorkspaceScreen.vue";

const REF = "TND-MOH-2027-033";
const BID = "BID-MOH-2027-033-001";
const STAGES = [["PREPARE", "Prepare bid"], ["SIGN_AND_SUBMIT", "Sign and submit"], ["RECEIPT", "Receipt"]];
const MARKERS = { done: "Done", current: "Current", blocked: "Blocked", not_started: "Not started" };
const LABELS = { your_turn: "Your turn", your_turn_blocked: "Your turn, blocked", waiting: "Waiting on someone", done: "Done" };

function journey(markers, holder = "") {
	const at = Math.max(0, markers.findIndex((m) => m === "current" || m === "blocked"));
	const stages = STAGES.map(([code, label], i) => ({ code, label, marker: markers[i], marker_label: MARKERS[markers[i]], holder: i === at && markers[i] !== "done" ? holder : "" }));
	const parts = { prefix: `Stage ${at + 1} of 3: `, label: STAGES[at][1], suffix: holder ? ` — ${holder}` : "" };
	return { stages, current: STAGES[at][0], reduced_style: "stage_of", reduced: false, reduced_text: parts.prefix + parts.label + parts.suffix, reduced_parts: parts, upstream: null, downstream: null };
}
function answer(kind, headline, extra = {}) {
	return { kind, label: LABELS[kind], headline, sentence: "", stage: "", holder: null, since: null, blockers: [], fixes: [], primary_action: "", ...extra };
}
const TASK_LABELS = [["documents", "Tender documents, clarifications and addenda"], ["company", "Company, declarations and tender security"], ["requirements", "Requirements and supporting evidence"], ["price", "Price"], ["review", "Review and submit"]];
function tasks(states, updated, { closed = false } = {}) {
	return TASK_LABELS.map(([key, label], i) => {
		const status = states[i];
		const action = closed ? { label: "View", primary: false } : key === "review" ? (status === "Complete" ? { label: "Review bid", primary: true } : { label: "View", primary: false }) : { label: status === "Complete" ? "View" : "Continue", primary: false };
		return { key, label, purpose: "", status, must_fix: 0, review_notes: 0, updated_label: updated[i] || "—", action: { ...action, href: `/tenders/${REF}/bid/${key}` } };
	});
}
const DONE_TIMES = ["1 Jun 2027, 12:10", "10 Jun 2027, 10:05", "10 Jun 2027, 11:30", "10 Jun 2027, 12:15", "10 Jun 2027, 13:50"];
const NOTICES = [
	{ key: "ANS-1", label: "Clarification answer · 26 May 2027", status: "Delivered", tone: "live", action: { label: "View answer", href: `/tenders/${REF}/bid/documents` } },
	{ key: "ADD-MOH-2027-033-001", label: "ADD-MOH-2027-033-001 · Delivery point clarified", status: "Acknowledged", tone: "live", action: { label: "View addendum", href: "/api/method/x?key=ADD&inline=1" } },
];
const DEADLINE = { rows: [{ label: "Submissions close", value: "12 Jun 2027, 11:00 EAT" }, { label: "Time remaining", value: "Closes in 1 day 20 hours 40 minutes" }] };
const HEADER = (action, version = 7) => ({ title_line: "Supply and delivery of business laptops", refs_line: `${REF} · ${BID} · Draft Version ${version}`, description: "Complete the five tasks below before an Authorised Signatory submits the bid.", action });
const REVIEW = { label: "Review bid", href: `/tenders/${REF}/bid/review`, tone: "primary" };
const SUPPORT = { label: "Supplier support", href: "mailto:supplier.support@kentender.example" };

function base(extra) {
	return {
		bid: { reference: BID, tender_reference: REF, status: "Ready to submit", draft_version: 7 }, tender: { reference: REF, title: "Supply and delivery of business laptops", deadline_label: "12 Jun 2027, 11:00 EAT" },
		header: HEADER(REVIEW), deadline: DEADLINE, availability_notice: null, notices: NOTICES,
		notices_note: "Delivery describes the notice sent to your Tender notice email. The published answer and addendum are available here whether or not a notice was delivered.",
		tasks: tasks(["Complete", "Complete", "Complete", "Complete", "Complete"], DONE_TIMES), saved_text: "Saved 10 Jun 2027, 13:50 EAT by David Ouma.",
		next_step: answer("waiting", "Authorised Signatory Mary Wanjiku must submit this bid."), journey: journey(["done", "current", "not_started"], "Mary Wanjiku"),
		...extra,
	};
}

/** One `get_bid_workspace` read for a board variant. */
export function workspace(variant = "") {
	switch (variant) {
		case "SIGNATORY":
			return base({ next_step: answer("your_turn", "Review, sign and submit this bid before 12 Jun 2027, 11:00 EAT."), journey: journey(["done", "current", "not_started"], "Mary Wanjiku") });
		case "IN-PROGRESS":
			return base({
				header: HEADER({ label: "Continue bid", href: `/tenders/${REF}/bid/requirements`, tone: "primary" }), saved_text: "",
				tasks: tasks(["Complete", "Complete", "Needs attention", "In progress", "Not started"], DONE_TIMES.slice(0, 2)),
				next_step: answer("your_turn", "Continue the requirements and evidence task.", { sentence: "Requirements and supporting evidence is outstanding; submissions close 12 Jun 2027, 11:00 EAT." }), journey: journey(["current", "not_started", "not_started"], "David Ouma"),
			});
		case "ADDENDUM": {
			const fix = { fix_id: "review_addendum", label: "Review addendum", responsibility: "Supplier user", person: "", kind: "route", target: `/tenders/${REF}/bid/documents`, primary: true };
			return base({
				header: HEADER({ label: "Review addendum", href: `/tenders/${REF}/bid/documents`, tone: "primary" }, 4), saved_text: "",
				deadline: { rows: [{ label: "Submissions close", value: "12 Jun 2027, 11:00 EAT" }, { label: "Time remaining", value: "Closes in 10 days 22 hours 55 minutes" }] },
				notices: [NOTICES[0], { ...NOTICES[1], status: "Not acknowledged", tone: "attention", action: { label: "Review addendum", href: `/tenders/${REF}/bid/documents` } }],
				tasks: tasks(["Needs attention", "Complete", "Needs attention", "In progress", "Not started"], []),
				next_step: answer("your_turn_blocked", "Review the changed delivery location and acknowledge the current addendum before submitting.", { blockers: [{ reason_code: "BDS_ADDENDUM_REVIEW_REQUIRED", message: "", headline: "", figures: {}, facts: [], fixes: [fix] }], fixes: [fix] }),
				journey: journey(["blocked", "not_started", "not_started"], "David Ouma"),
			});
		}
		case "GATE":
			return base({
				availability_notice: { tone: "critical", title: "Electronic bid submission is not available yet", text: "Your bid remains saved and has not been submitted. Submissions close 12 Jun 2027, 11:00 EAT.", links: [SUPPORT] },
				next_step: answer("waiting", "Release operator Nadia Kamau holds the verified production-submission release.", { sentence: "Your bid remains saved and no receipt exists." }), journey: journey(["done", "blocked", "not_started"], "Nadia Kamau"),
			});
		case "OUTAGE":
			return base({
				availability_notice: { tone: "critical", title: "Electronic submission is temporarily unavailable", text: "Your bid remains saved and no receipt exists. Submissions close 12 Jun 2027, 11:00 EAT.", links: [{ label: "View status", href: `/tenders/${REF}/bid/status` }, SUPPORT] },
				next_step: answer("waiting", "Technical operator Daniel Otieno is restoring electronic submission.", { sentence: "Your bid remains saved." }), journey: journey(["done", "blocked", "not_started"], "Daniel Otieno"),
			});
		case "CFG-PREP":
			return base({
				header: HEADER({ label: "Continue saved bid", href: `/tenders/${REF}/bid/requirements`, tone: "primary" }),
				availability_notice: { tone: "warning", title: "Submission is unavailable", text: "Supplier portal information is being restored. Your saved bid can still be reviewed and saved.", links: [] },
				tasks: tasks(["Complete", "Complete", "Needs attention", "In progress", "Not started"], DONE_TIMES.slice(0, 2)),
				next_step: answer("your_turn", "Continue your saved bid. Submission is blocked until supplier portal information is restored."), journey: journey(["current", "not_started", "not_started"], "David Ouma"),
			});
		case "CFG-READY":
			return base({
				header: HEADER({ label: "Continue saved bid", href: `/tenders/${REF}/bid/review`, tone: "secondary" }),
				next_step: answer("waiting", "CFG System Manager Daniel Otieno is restoring supplier portal information.", { sentence: "Your ready Draft remains saved." }), journey: journey(["done", "blocked", "not_started"], "Daniel Otieno"),
			});
		case "CLOSED":
			return base({
				header: HEADER({ label: "Back to My bids", href: "/my-bids", tone: "secondary" }),
				deadline: { rows: [{ label: "Submission deadline", value: "12 Jun 2027, 11:00 EAT" }, { label: "Trusted server time", value: "12 Jun 2027, 11:00:01 EAT" }] },
				tasks: tasks(["Complete", "Complete", "Complete", "Complete", "Complete"], DONE_TIMES, { closed: true }),
				next_step: answer("done", "Submission closed at 12 Jun 2027, 11:00 EAT; this Draft was not submitted."), journey: journey(["done", "not_started", "not_started"]),
			});
		case "WITHDRAWN-RELEASE":
			// §4.4.4 (TPR-CHG-001 v0.13): the Draft is kept for reading while the Tender's Procurement Officer holds the resolution
			return base({
				header: { ...HEADER(null), action: null },
				tasks: tasks(["Complete", "Complete", "Complete", "Complete", "Complete"], DONE_TIMES, { closed: true }),
				guidance_links: [{ label: "View current Tender", href: `/tenders/${REF}` }, SUPPORT],
				next_step: answer("waiting", "Procurement Officer Brian Wafula holds the governed Tender resolution; this Draft is saved but cannot be submitted against the withdrawn format."),
				journey: journey(["blocked", "not_started", "not_started"], "Brian Wafula"),
			});
		default:
			return base({});
	}
}

const VARIANTS = [
	["BDS-DES-06 / BDS-DES-06-REPRESENTATIVE", ""], ["BDS-DES-06-SIGNATORY", "SIGNATORY"], ["BDS-DES-06-IN-PROGRESS", "IN-PROGRESS"], ["BDS-DES-06-ADDENDUM", "ADDENDUM"],
	["BDS-DES-06-GATE", "GATE"], ["BDS-DES-06-OUTAGE", "OUTAGE"], ["BDS-DES-06-CFG-INCOMPLETE · in preparation", "CFG-PREP"], ["BDS-DES-06-CFG-INCOMPLETE · ready", "CFG-READY"],
	["BDS-DES-06-CLOSED-UNSUBMITTED", "CLOSED"], ["BDS-DES-06-WITHDRAWN-RELEASE", "WITHDRAWN-RELEASE"],
];
export const WORKSPACE_VARIANTS = VARIANTS.map(([label]) => label);

export const SCREENS = ["desktop", "narrow"].flatMap((frame) =>
	VARIANTS.map(([variant, key]) => ({ name: "BidWorkspaceScreen", variant, frame, component: BidWorkspaceScreen, props: { initial: workspace(key), reference: REF, bid: BID }, path: `/tenders/${REF}/bid` })),
);
