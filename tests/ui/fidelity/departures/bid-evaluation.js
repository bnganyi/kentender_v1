// Structural departures for the Bid Evaluation screens (EVL-CHG-001 v0.4,
// boards in `docs/mvp-1-r1/15_bid_evaluation/design/Bid Evaluation Artboards.dc.html`,
// drawn by `evl/evl-kit.js` from `evl/boards-*.js` and addressed by board id).
//
// Keyed by board id. Every entry names what the build adds or omits that the
// board does not draw, why, and the authority for it. Unregistered additions
// fail; stale entries fail too. Never resolve a departure by deleting an
// enhancement the spec requires.

export const DEPARTURES = {};

// Boards compared by `public/js/bid_evaluation/bid-evaluation.fidelity.spec.js`.
export const COVERED = [
	"D02-A",
	"D02-S",
	"D02-D",
	"D02-CONFLICT",
	"D02-REPLACE",
	"D02-INTAKE-FIRST",
	"D02-INTAKE-FIRST-HOP",
	"D02-UNABLE",
	"D02-NO-BIDS",
	"S-OPENING-AWAITED",
	"D03",
	"D03-READY",
	"D04",
	"D04-AUTO",
	"D04-CONCERN",
	"D04-FAIL",
	"D05-START",
	"D05-JOIN",
	"D05",
	"D05-CONCLUSION",
	"D05-CHAIR",
	"D05-MEMBER",
	"D05-DISAGREE",
	"D05-RECORD",
	"D05-RECORD-MEMBER",
	"D05-RECORD-AUDITOR",
	"D06-SEND",
	"D06-OUTCOME",
	"D07-DRAFT",
	"D07-PREVIEW",
	"D07-SIGN",
	"D07-CONCERN",
	"D07-REVISE",
	"D07-REVISE-DLG",
	"D07-WAIT",
	"D07-SENT",
	"D07-HOP",
	"D07-HOP-RETURN",
	"S-AUDITOR",
	"D08-PAUSED",
	"D08-CANCELLED",
];
