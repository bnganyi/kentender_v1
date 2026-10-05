// Structural departures for the Tenders screens (TPR-CHG-001 v0.12, boards in
// `docs/mvp-1-r1/11_tenders/design/`, one board per file, addressed by their
// `data-screen-label`).
//
// Keyed `Component#variant`. Every entry names what the build adds or omits
// that the board does not draw, why, and the authority for it. Unregistered
// additions fail; stale entries fail too. Never resolve a departure by
// deleting an enhancement the spec requires.

// The boards export the frame as `card blueprint elev-sm` without its four
// corner marks; the Industry `.blueprint` frame draws them (BlueprintCard).
const CORNERS = {
	path: "card+blueprint > corner",
	because: "The Industry blueprint frame's four corner marks; the board export draws the frame without them.",
	authority: "KenTender Industry design system — .blueprint + .corner (AGENTS.md §6.6 shipped defect: frame without corners)",
};

// TPR-CHG-001 v0.12 plan W1: where the board regeneration dropped approved
// spec content, the content is restored and registered here.
const W1 = "TPR-CHG-001 v0.12 plan W1 — boards govern structure, the spec governs content";

// The TPR-DES-14 board lays every common state out on one sheet under its own
// title; the live screen is one state's card alone.
const STATE_SHEET = {
	omits: ["h1"],
	because: "The board sheet's own title (\"Common states\") above the list of variants; a live state is its card alone.",
	authority: "TPR-CHG-001 v0.12 §10.15 — each is a full inline state",
};

export const DEPARTURES = {
	"EditorScreen#TPR-DES-03": [CORNERS],
	"EditorScreen#TPR-DES-03-PHYSICAL": [CORNERS],
	"EditorScreen#TPR-DES-03-ONLINE": [CORNERS],
	"EditorScreen#TPR-DES-04": [CORNERS],
	"EditorScreen#TPR-DES-04-RETURNED": [CORNERS],
	"ReviewScreen#TPR-DES-05": [CORNERS],
	"ReviewScreen#TPR-DES-05-NEEDS-ATTENTION": [CORNERS],
	"ApprovalScreen#TPR-DES-06": [CORNERS],
	"ApprovalScreen#TPR-DES-06-SEGREGATION": [CORNERS],
	"AuthorisationScreen#TPR-DES-07": [CORNERS],
	"AuthorisationScreen#TPR-DES-07-SEGREGATION": [CORNERS],
	"PublicationScreen#TPR-DES-08": [CORNERS],
	"PublicationScreen#TPR-DES-08-INVALID": [CORNERS],
	"PublicationScreen#TPR-DES-08-CONFLICT": [CORNERS],
	"PublishedScreen#TPR-DES-09-HOPF": [CORNERS],
	"PublishedScreen#TPR-DES-09-AO": [CORNERS],
	"PublishedScreen#TPR-DES-09-PO": [CORNERS],
	"PublishedScreen#TPR-DES-09-READER": [CORNERS],
	"PublishedScreen#TPR-DES-09-HOPF-NO-ADDENDUM": [CORNERS],
	"PublishedScreen#TPR-DES-09-HOPF-ENDED": [CORNERS],
	"ClarificationScreen#TPR-DES-11": [CORNERS],
	"ClarificationScreen#TPR-DES-11-FAILURE": [CORNERS],
	"AddendumScreen#TPR-DES-10-DRAFT": [CORNERS],
	"AddendumScreen#TPR-DES-10-HOPF": [CORNERS],
	"AddendumScreen#TPR-DES-10-AWAITING": [CORNERS],
	"AddendumScreen#TPR-DES-10-ISSUED": [CORNERS],
	"AddendumScreen#TPR-DES-10-MATERIAL": [CORNERS],
	"AddendumScreen#TPR-DES-10-MATERIAL-WAIT": [CORNERS],
	"AddendumScreen#TPR-DES-10-MATERIAL-CLOSED": [CORNERS],
	"CancelScreen#TPR-DES-12-BASE": [CORNERS],
	"CancelScreen#TPR-DES-12-RECOMMEND": [CORNERS],
	"CancelScreen#TPR-DES-12-REQUEST": [CORNERS],
	"CancelScreen#TPR-DES-12-CANCELLED-HOLDER": [CORNERS],
	"CancelScreen#TPR-DES-12-CANCELLED-READER": [CORNERS],
	"CorrectionRequestedScreen#TPR-DES-13-REQUESTED": [CORNERS],
	"CorrectionRequestedScreen#TPR-DES-13-SUCCESSOR": [CORNERS],
	...Object.fromEntries(["READY", "DRAFT", "RETURNED", "HOPF", "AO", "PUBLISHING", "PUBLISHED", "READER", "EMPTY"].map((v) => [`WorkspaceScreen#TPR-DES-01-${v}`, [CORNERS]])),
	"StartTenderDialog#TPR-DES-02-SUPPORTED": [],
	"StartTenderDialog#TPR-DES-02-UNSUPPORTED": [],
	...Object.fromEntries(["forbidden", "not-found", "requisition-unavailable", "release-superseded", "rule-unavailable", "stale", "failure"].map((kind) => [`CommonState#TPR-DES-14-${kind}`, [STATE_SHEET, { ...CORNERS, path: "card+blueprint > corner" }]])),
};

export const COVERED = Object.keys(DEPARTURES);
export { W1 };
