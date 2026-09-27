// Structural departures for the Bid Submission portal screens (BDS-CHG-001
// v0.8, boards "Bid Board v3 - A…E" in `docs/mvp-1-r1/12_bid_submission/design/`,
// addressed by `data-screen-label`, compared at the 1440 desktop frame and
// the 390 narrow frame).
//
// Keyed `Component#variant@frame`. Every entry names what the build adds or
// omits that the board does not draw, why, and the authority for it.
// Unregistered differences fail; stale entries fail too.

// Not a structural departure, recorded for the redraw: BDS-DES-02-JV-START
// names the "Who is bidding?" step in its caption only and draws the base
// page. The step is built from BDS-CHG-001 §10.3 as a dialog over the
// overview (StartBidDialog.vue); the artboard compared is the page beneath it
// (FU-V08-46).

export const DEPARTURES = {};

// Every `Component#variant@frame` the structural spec compares.
export const COVERED = new Set([
	...["desktop", "narrow"].flatMap((frame) => ["BDS-DES-01", "BDS-DES-01-EMPTY"].map((v) => `AvailableTendersScreen#${v}@${frame}`)),
	...["desktop", "narrow"].flatMap((frame) =>
		["", "-SIGNED-OUT", "-JV-START", "-DRAFT", "-SUBMITTED", "-CANDIDATE-QUESTION", "-CANCELLED"].map((v) => `TenderOverviewScreen#BDS-DES-02${v}@${frame}`),
	),
]);
