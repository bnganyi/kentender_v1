// Structural departures for the Tenders screens (TPR-CHG-001 v0.12, boards in
// `docs/mvp-1-r1/11_tenders/design/`, one board per file, addressed by their
// `data-screen-label`).
//
// Keyed `Component#variant`. Every entry names what the build adds or omits
// that the board does not draw, why, and the authority for it. Unregistered
// additions fail; stale entries fail too. Never resolve a departure by
// deleting an enhancement the spec requires.

// The boards export the frame as `card blueprint elev-sm` without its four
// corner marks; the Industry `.kt-blueprint` frame draws them (BlueprintCard).
const CORNERS = {
	path: "card+blueprint > corner",
	because: "The Industry blueprint frame's four corner marks; the board export draws the frame without them.",
	authority: "KenTender Industry design system — .kt-blueprint + .kt-corner (AGENTS.md §6.6 shipped defect: frame without corners)",
};

// TPR-CHG-001 v0.12 plan W1: where the board regeneration dropped approved
// spec content, the content is restored and registered here.
const W1 = "TPR-CHG-001 v0.12 plan W1 — boards govern structure, the spec governs content";

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
};

export const COVERED = Object.keys(DEPARTURES);
export { W1 };
