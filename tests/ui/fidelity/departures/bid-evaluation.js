// Structural departures for the Bid Evaluation screens (EVL-CHG-001 v0.4,
// boards in `docs/mvp-1-r1/15_bid_evaluation/design/Bid Evaluation Artboards.dc.html`,
// drawn by `evl/evl-kit.js` from `evl/boards-*.js` and addressed by board id).
//
// Keyed by board id. Every entry names what the build adds or omits that the
// board does not draw, why, and the authority for it. Unregistered additions
// fail; stale entries fail too. Never resolve a departure by deleting an
// enhancement the spec requires.

const NARRATIVE = {
	reason: "The secretary's committee summary stays editable in every draft, with the report history beside it (the only editable part of the report; board D07-DRAFT draws both). This outcome variant redraws the draft without them.",
	authority: "EVL-CHG-001 v0.4 §5.5 (only the narrative is editable); board D07-DRAFT",
};

export const DEPARTURES = {
	"S-STALE-RECORD": [
		{ path: "h2", reason: "The stale warning is shown over the whole draft the secretary was working on (summary and sections kept), not a reduced page: the page and the unsent summary are revalidated in place.", authority: "AGENTS.md §6.4 (revalidate in place; keep unsent input)" },
		{ path: "disclosure", reason: "As above: the report history stays with the draft under the stale warning.", authority: "AGENTS.md §6.4" },
	],
	"D06-WITHDRAW-DLG": [
		{ path: "group", reason: "The dialog opens over the same request page as board D06-WITHDRAW, which shows the chair's recorded reason; the dialog board redrew that page without it.", authority: "board D06-WITHDRAW" },
	],
	"D07-NO-RESPONSIVE": [{ path: "disclosure", ...NARRATIVE }],
	"D07-NO-AGREEMENT": [{ path: "field", ...NARRATIVE }, { path: "disclosure", ...NARRATIVE }],
	"D07-EXPIRED": [{ path: "field", ...NARRATIVE }, { path: "disclosure", ...NARRATIVE }],
	"D07-OVERDUE-SEC": [{ path: "field", ...NARRATIVE }, { path: "disclosure", ...NARRATIVE }],
};

// Boards compared by `public/js/bid_evaluation/bid-evaluation.fidelity.spec.js`.
// Not compared yet, with the reason:
//   D01-EMPTY, D01-FILTERED — need a register the browser world never has
//     (no readable evaluation; a search with no match); owed with the demo profiles.
//   S-FORBIDDEN — the forbidden workspace needs a viewer with no evaluation
//     responsibility; owed with the persona pass.
//   S-CHECKS — unreachable in this build: intake and the automatic checks
//     commit together, so there is no "checks running" state to show.
//   S-SOURCE-OPEN — the same failed-intake state as D08-SOURCE (compared);
//     the board is a second framing of it for the secretary.
//   D03-FUNDING, D03-TIE, D07-TIE, D07-FUNDING — need a second bid or a
//     budget reservation in the browser world (tender 036 and funding worlds).
//   D07-EXPIRED-SIGN, D07-EXPIRED-SENT — need the expired world signed.
//   D08-RULE — needs a rules file without the storage rule.
export const COVERED = [
	"D06-SUPPLIER", "D06-RECEIVED", "D06-LATE", "D06-LATE-RECEIVED", "D06-CLOSED", "D06-FINAL-CLOSED", "D06-FINAL-CLOSED-NR",
	"D02-A",
	"D02-S",
	"D02-D",
	"D02-CONFLICT",
	"D02-REPLACE",
	"D02-INELIGIBLE",
	"D02-INTAKE-FIRST",
	"D02-INTAKE-FIRST-HOP",
	"D02-DECLARE-FIRST",
	"D02-UNABLE",
	"D02-NO-BIDS",
	"S-LOADING",
	"S-ERROR",
	"S-NOT-FOUND",
	"S-OPENING-AWAITED",
	"S-STALE-RECORD",
	"S-STALE-REPORT",
	"S-UNCONFIRMED",
	"D03",
	"D03-READY",
	"D04",
	"D04-AUTO",
	"D04-CONCERN",
	"D04-FAIL",
	"D05-START",
	"D05-JOIN",
	"D05",
	"D05-ABSENT",
	"D05-ABSENT-CHAIR",
	"D05-ABSENT-MEMBER",
	"D05-CONCLUSION",
	"D05-CONCLUSION-Q",
	"D05-CHAIR",
	"D05-MEMBER",
	"D05-DISAGREE",
	"D05-RECORD",
	"D05-RECORD-MEMBER",
	"D05-RECORD-AUDITOR",
	"D06-SEND",
	"D06-DELIVERY",
	"D06-WITHDRAW",
	"D06-WITHDRAW-DLG",
	"D06-OUTCOME",
	"D06-NO-REPLY",
	"D06-LATE-REVIEW",
	"D06-CHANGED-OFFER",
	"D07-DRAFT",
	"D07-PREVIEW",
	"D07-INCOMPLETE",
	"D07-NO-RESPONSIVE",
	"D07-NO-AGREEMENT",
	"D07-OVERDUE",
	"D07-OVERDUE-SEC",
	"D07-EXPIRED",
	"D07-SIGN",
	"D07-CONCERN",
	"D07-REVISE",
	"D07-REVISE-DLG",
	"D07-WAIT",
	"D07-DELIVERY",
	"D07-SENT",
	"D07-HOP",
	"D07-HOP-RETURN",
	"D07-RETURNED",
	"D07-DECISION-UNKNOWN",
	"D07-DECISION-UNKNOWN-CHAIR",
	"S-AUDITOR",
	"D08-SOURCE",
	"D08-VERIFY-PLAN",
	"D08-DD",
	"D08-DD-FREEZE",
	"D08-DD-SIGN",
	"D08-VERIFY-OUTCOME",
	"D08-VERIFY-NEG",
	"D08-SUPPLEMENT",
	"D08-SUPPLEMENT-SENT",
	"D08-SUPPLEMENT-HOP",
	"D08-CORRECTION",
	"D08-CORRECTION-HOP",
	"D08-PAUSED",
	"D08-CANCELLED",
	"P-PREP",
	"P-SIGN",
	"C-PREP",
	"C-SIGN",
	"D01",
	"D01-APPOINT",
	"D01-APPOINT-HOP",
];
