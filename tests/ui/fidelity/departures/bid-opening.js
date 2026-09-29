// Structural departures for the Bid Opening screens (BOP-CHG-001 v0.10, boards
// in `docs/mvp-1-r1/14_bid_opening/design/Bid Opening Artboards v0.9.2.dc.html`,
// addressed by board id).
//
// Keyed by board id. Every entry names what the build adds or omits that the
// board does not draw, why, and the authority for it. Unregistered additions
// fail; stale entries fail too. Never resolve a departure by deleting an
// enhancement the spec requires.

export const DEPARTURES = {};

// Boards compared by `public/js/bid_opening/bid-opening.fidelity.spec.js`.
// Not compared, with the reason (artboard_inventory.md "Replaced"):
//   c10b — after a member rejoins, the opening resumes into the ordinary
//          in-session view for where it stopped (c9 here); the board's "Record
//          the request" prompt refers to an attendee request the server does
//          not hold as pending (a request is recorded by the recorder when it
//          is made, board c7).
export const COVERED = [
	"a1", "a2", "a3", "a4", "a5",
	"c1", "c2", "c2b", "c2c", "c2d", "c3", "c4", "c5", "c6", "c7", "c8", "c8b", "c13", "c13b", "c9", "c10", "c11", "c11b", "c11c", "c11e", "c11d", "c12",
	"z1", "n1", "n2",
	"r1", "r2", "r3", "r4", "r5",
	"r6", "h1", "h2", "h3", "h4", "h5",
];

// The public opening page (boards p0–p6), compared by
// `public/js/bid_opening/portal/public-opening.fidelity.spec.js`.
export const PUBLIC_DEPARTURES = {};
export const PUBLIC_COVERED = ["p0", "p1a", "p1", "p2", "p3", "p4", "p5", "p6"];
