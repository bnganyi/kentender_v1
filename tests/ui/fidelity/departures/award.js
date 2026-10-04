// Structural departures for the Award screens (AWD-CHG-001 v0.4, boards in
// `docs/mvp-1-r1/16_award/design/Award Artboards.dc.html`, the inline `BOARDS`
// array drawn by one `<x-dc>` template, addressed by board id).
//
// Keyed by board id. Every entry names what the build adds or omits that the
// board does not draw, why, and the authority for it. Unregistered additions
// fail; stale entries fail too. Never resolve a departure by deleting an
// enhancement the spec requires.

export const DEPARTURES = {
	V23p: [
		{ path: "region", reason: "The Accounting Officer's decision reasons are recorded with the corrected award (the board draws the combined action with no reason field; D03 draws the same Decision reason field for the initial award).", authority: "AWD-CHG-001 v0.4 §4 Decision (reasons), §7 RecordAwardCorrectionDecision; board D03" },
		{ path: "region/h2", reason: "As above: the Decision section's heading.", authority: "board D03" },
		{ path: "region/field", reason: "As above: the Decision reason field.", authority: "board D03" },
	],
};

// Boards compared by `public/js/award/award.fidelity.spec.js`: all 47, each
// from a captured synthetic world (award.seeds.playwright_ui_fixtures).
// Page boards are compared page for page; dialog boards (X01–X11) are
// compared dialog for dialog, because the live dialog opens over the page
// the user was on, not over the board's bare header.
export const COVERED = [
	"D01", "D01e", "D02", "D03", "D04", "D05", "D06", "D07", "D07c",
	"V01", "V02", "V03", "V04", "V05", "V06", "V07", "V08", "V09", "V10", "V11", "V12", "V13", "V14", "V15", "V15s", "V16", "V17", "V18", "V19", "V20", "V21",
	"V22", "V23", "V23p", "V24", "V25",
	"X01", "X02", "X03", "X04", "X05", "X06", "X07", "X08", "X09", "X10", "X11",
];
