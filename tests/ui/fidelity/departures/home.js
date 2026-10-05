// Structural departures for the Home page (HOME-CHG-001 v0.6 §10B; the sixteen boards in
// `docs/mvp-1-r1/18_home_page/design/Home/Home.dc.html`, each a `<div id="HOME-DES-nn">`), compared by
// `kentender_core/kentender_core/public/js/home/Home.fidelity.spec.js` against the page mounted on the payload each
// board draws (`public/js/home/fixtures/boards.js`).
//
// Keyed by board id. Every entry says where the page differs from the board, why, and on whose authority.
// Unregistered differences fail; a stale entry fails too. Never resolve a departure by deleting what the spec requires.
export const DEPARTURES = {
	// A technical reader has no oversight rows, so the Analytics link (the one every other reader gets after Records you
	// oversee) sits in the header row beside Technical record search. Board 27 draws only the search link.
	"HOME-DES-27": [
		{
			text: "Procurement Analytics",
			path: "header (a quiet Procurement Analytics link beside Technical record search)",
			reason:
				"ANL-CHG-001 v0.8 lets the Technical Operator and the other technical readers read every Analytics figure site-wide, and Home's one Analytics link follows the server's verdict. Technical readers see no region to carry it, so it is a quiet header link. Board 27 predates that decision.",
			authority: "ANL-CHG-001 v0.8 D-ANL-10; ANL tracker gate ANL-G06 (the Home link switched to the server's verdict, 5 October 2026). Owner confirmation of the header placement: FU-HOME-43",
		},
	],
};

// All sixteen boards, in the order the board file draws them.
export const COVERED = [
	"HOME-DES-21", "HOME-DES-21N", "HOME-DES-29", "HOME-DES-22", "HOME-DES-23", "HOME-DES-24", "HOME-DES-25", "HOME-DES-26",
	"HOME-DES-26B", "HOME-DES-27", "HOME-DES-28A", "HOME-DES-28B", "HOME-DES-28C", "HOME-DES-28D", "HOME-DES-28E", "HOME-DES-28F",
];
