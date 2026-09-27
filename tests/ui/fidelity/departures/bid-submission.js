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
//
// Likewise BDS-DES-07-QUESTION-OPEN-DIALOG and its success state draw the
// unchanged documents task beneath the Ask-a-question dialog; the page is
// compared (the dialog is QuestionDialog.vue, shared with the overview).

export const DEPARTURES = {};

// Every `Component#variant@frame` the structural spec compares.
export const COVERED = new Set([
	...["desktop", "narrow"].flatMap((frame) => ["BDS-DES-01", "BDS-DES-01-EMPTY"].map((v) => `AvailableTendersScreen#${v}@${frame}`)),
	...["desktop", "narrow"].flatMap((frame) =>
		["", "-SIGNED-OUT", "-JV-START", "-DRAFT", "-SUBMITTED", "-CANDIDATE-QUESTION", "-CANCELLED"].map((v) => `TenderOverviewScreen#BDS-DES-02${v}@${frame}`),
	),
	...["desktop", "narrow"].flatMap((frame) => [
		...["", "-SUBMITTED", "-WITHDRAWN", "-EMPTY"].map((v) => `MyBidsScreen#BDS-DES-05${v}@${frame}`),
		...["", "-EMPTY", "-SUSPENDED"].map((v) => `ReceiptHistoryScreen#BDS-DES-17${v}@${frame}`),
		...[
			"BDS-DES-06 / BDS-DES-06-REPRESENTATIVE", "BDS-DES-06-SIGNATORY", "BDS-DES-06-IN-PROGRESS", "BDS-DES-06-ADDENDUM", "BDS-DES-06-GATE", "BDS-DES-06-OUTAGE",
			"BDS-DES-06-CFG-INCOMPLETE · in preparation", "BDS-DES-06-CFG-INCOMPLETE · ready", "BDS-DES-06-CLOSED-UNSUBMITTED",
		].map((v) => `BidWorkspaceScreen#${v}@${frame}`),
		...[
			"BDS-DES-07", "BDS-DES-07-COMPLETE", "BDS-DES-07-QUESTION-OPEN / BDS-DES-07-NONE", "BDS-DES-07-QUESTION-OPEN-DIALOG", "BDS-DES-07-QUESTION-OPEN-DIALOG · success",
			"BDS-DES-07-CLOSED", "BDS-DES-07 notice pending · Queued", "BDS-DES-07 notice pending · Sent", "BDS-DES-07-NOTICE",
		].map((v) => `DocumentsTaskScreen#${v}@${frame}`),
		...["BDS-DES-08", "BDS-DES-08-SECURITY", "BDS-DES-08-JV", "BDS-DES-08-ACCOUNT-UPDATE"].map((v) => `CompanyTaskScreen#${v}@${frame}`),
	]),
	...["desktop", "narrow"].flatMap((frame) => [
		...["BDS-DES-03", "BDS-DES-03-VERIFY"].map((v) => `RegisterScreen#${v}@${frame}`),
		...["", "-ATTENTION", "-VERIFY", "-SUSPENDED"].map((v) => `AccountScreen#BDS-DES-04${v}@${frame}`),
	]),
]);

// The supplier Account screens (kentender_suppliers), compared by their own spec.
export const ACCOUNT_SCREENS = /^(RegisterScreen|AccountScreen)#/;
