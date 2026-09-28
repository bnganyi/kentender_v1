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
//
// BDS-DES-16 is one catalogue sheet of cells, not a page per state; each live
// state is compared with its cell by text in
// kentender_procurement/public/js/bid_portal/common-states.fidelity.spec.js.
//
// BDS-DES-12 confirmation dialog draws the Submit page beneath the "Submit
// this bid?" dialog; the page is compared (the dialog is ConfirmSubmitDialog.vue).

// Board D draws BDS-DES-14-REPLACED and the page beneath the withdrawal
// dialog as abbreviated receipts. BDS-CHG-001 §10.15 says the replacement
// receipt reuses the receipt composition (§10.14), and §10.19 puts the next
// step on every bid page, so the build carries them.
const RECEIPT_GUIDANCE = [
	{ path: "journey", because: "The bid journey on every bid page; the abbreviated receipt artboard leaves it out.", authority: "BDS-CHG-001 v0.8 §10.15 (reuse receipt composition) and §10.19" },
	{ path: "next-step", because: "The §10.19 next step on every bid page; the abbreviated receipt artboard leaves it out.", authority: "BDS-CHG-001 v0.8 §10.15 (reuse receipt composition) and §10.19" },
];
const RECEIPT_NOTICE = {
	path: "notice",
	because: "The receipt's \"confirms submission only\" notice; the page beneath the withdrawal dialog is drawn without it.",
	authority: "BDS-CHG-001 v0.8 §10.14 item 3",
};

export const DEPARTURES = Object.fromEntries(
	["desktop", "narrow"].flatMap((frame) => [
		[`ReceiptScreen#BDS-DES-14-REPLACED@${frame}`, RECEIPT_GUIDANCE],
		[`ReceiptScreen#BDS-DES-14 withdrawal dialog@${frame}`, [...RECEIPT_GUIDANCE, RECEIPT_NOTICE]],
	]),
);

// Every `Component#variant@frame` the structural spec compares.
export const COVERED = new Set([
	...["desktop", "narrow"].flatMap((frame) => ["BDS-DES-01", "BDS-DES-01-EMPTY"].map((v) => `AvailableTendersScreen#${v}@${frame}`)),
	...["desktop", "narrow"].flatMap((frame) =>
		["", "-SIGNED-OUT", "-JV-START", "-DRAFT", "-SUBMITTED", "-CANDIDATE-QUESTION", "-CANCELLED", "-SUPERSEDED", "-WITHDRAWN-RELEASE"].map((v) => `TenderOverviewScreen#BDS-DES-02${v}@${frame}`),
	),
	...["desktop", "narrow"].flatMap((frame) => [
		...["", "-SUBMITTED", "-WITHDRAWN", "-EMPTY"].map((v) => `MyBidsScreen#BDS-DES-05${v}@${frame}`),
		...["", "-EMPTY", "-SUSPENDED"].map((v) => `ReceiptHistoryScreen#BDS-DES-17${v}@${frame}`),
		...[
			"BDS-DES-06 / BDS-DES-06-REPRESENTATIVE", "BDS-DES-06-SIGNATORY", "BDS-DES-06-IN-PROGRESS", "BDS-DES-06-ADDENDUM", "BDS-DES-06-GATE", "BDS-DES-06-OUTAGE",
			"BDS-DES-06-CFG-INCOMPLETE · in preparation", "BDS-DES-06-CFG-INCOMPLETE · ready", "BDS-DES-06-CLOSED-UNSUBMITTED", "BDS-DES-06-WITHDRAWN-RELEASE",
		].map((v) => `BidWorkspaceScreen#${v}@${frame}`),
		...[
			"BDS-DES-07", "BDS-DES-07-COMPLETE", "BDS-DES-07-QUESTION-OPEN / BDS-DES-07-NONE", "BDS-DES-07-QUESTION-OPEN-DIALOG", "BDS-DES-07-QUESTION-OPEN-DIALOG · success",
			"BDS-DES-07-CLOSED", "BDS-DES-07 notice pending · Queued", "BDS-DES-07 notice pending · Sent", "BDS-DES-07-NOTICE",
		].map((v) => `DocumentsTaskScreen#${v}@${frame}`),
		...["BDS-DES-08", "BDS-DES-08-SECURITY", "BDS-DES-08-JV", "BDS-DES-08-ACCOUNT-UPDATE"].map((v) => `CompanyTaskScreen#${v}@${frame}`),
		...["BDS-DES-09", "BDS-DES-09 response drawer", "BDS-DES-09-ATTENTION", "BDS-DES-09-ADDENDUM"].map((v) => `RequirementsTaskScreen#${v}@${frame}`),
		...["BDS-DES-10", "BDS-DES-10-INCOMPLETE"].map((v) => `PriceTaskScreen#${v}@${frame}`),
		...[
			"BDS-DES-11", "BDS-DES-11-EVIDENCE-ATTENTION", "BDS-DES-11-ADDENDUM-ATTENTION", "BDS-DES-11-REPRESENTATIVE", "BDS-DES-11-CFG · in preparation", "BDS-DES-11-CFG · ready",
		].map((v) => `ReviewTaskScreen#${v}@${frame}`),
		...[
			"BDS-DES-12", "BDS-DES-12 confirmation dialog", "BDS-DES-12-PENDING", "BDS-DES-12-CERTIFICATE", "BDS-DES-12-SIGNATURE", "BDS-DES-12-SERVICE", "BDS-DES-12-REJECTED", "BDS-DES-12-CFG",
			"BDS-DES-12-GATE",
		].map((v) => `SubmitScreen#${v}@${frame}`),
		...["BDS-DES-13", "BDS-DES-13-REPRESENTATIVE", "BDS-DES-13-CLOSED", "BDS-DES-14-REPLACED", "BDS-DES-14 withdrawal dialog", "BDS-DES-14-WITHDRAWN"].map((v) => `ReceiptScreen#${v}@${frame}`),
		`ReplacementScreen#BDS-DES-14@${frame}`,
	]),
	...["desktop", "narrow"].flatMap((frame) => [
		...["BDS-DES-03", "BDS-DES-03-VERIFY"].map((v) => `RegisterScreen#${v}@${frame}`),
		...["", "-ATTENTION", "-VERIFY", "-SUSPENDED"].map((v) => `AccountScreen#BDS-DES-04${v}@${frame}`),
	]),
]);

// The supplier Account screens (kentender_suppliers), compared by their own spec.
export const ACCOUNT_SCREENS = /^(RegisterScreen|AccountScreen)#/;
