// Structural departures for the Analytics page (ANL-CHG-001 v0.8 section 10A; the 22 boards drawn by the six files in
// `docs/mvp-1-r1/19_analytics/design/Analytics/`, each a `<div id="ANL-DES-nn">`), compared by
// `kentender_core/kentender_core/public/js/analytics/analytics.fidelity.spec.js` against the page mounted on the
// board's own captured server answer (`public/js/analytics/fixtures/ANL-DES-*.json`).
//
// Keyed by board id. Every entry says where the page differs from the board (`path`, a landmark path or a
// landmark text), why, and on whose authority. Unregistered differences fail; a stale entry fails too. Never resolve
// a departure by deleting what the spec requires.
//
// Kinds of entry:
//   { tag: "<landmark>", path }      the page builds that landmark from another element than the board's
//   { text, omitsText: [...], path }  the page says something other than the board in a landmark text
//
// What the comparison covers (and so what a departure can be about): the board's container skeleton (headings,
// tabs, fields, the register table, summary columns, empty states, the disclosure with its head, title row,
// chevron and body), the elements those landmarks are built from, and the ordered landmark texts (headings,
// labels, tabs, table headings, buttons, links, a summary column's heading, the disclosure title, an empty
// state's sentence and each outstanding-work row's sentence). Not covered, so not registered: the figures, rows
// and chart values (the page draws what the payload carries; the goldens are the server's own answers), layout
// and colour (inline styles on the boards, classes `kt-ap-*` on the page), and the charts' internals (their own specs).

const DISCLOSURE = [
	{
		tag: "disclosure",
		path: "disclosure (<details> on the board, <div> in the page)",
		reason:
			"The board draws the definitions as a native `<details class=\"kt-disclosure\">` with a `<summary>` head. The page draws a `<div class=\"kt-disclosure\">` whose head is a `<button aria-expanded aria-controls>`, because ANL section 11 asks for a disclosure that toggles and the page tests assert aria-expanded; every class, nesting and text is the board's.",
		authority: "ANL-CHG-001 v0.8 section 11 (How these figures are counted: toggle supplied definitions); KT-STD-001 accessibility rules for disclosures; Analytics.spec.js keyboard and aria-expanded tests",
	},
	{
		tag: "disclosure-head",
		path: "disclosure > disclosure-head (<summary> on the board, <button> in the page)",
		reason: "As above: the head is a real button that carries aria-expanded and names the region it controls, which a `<summary>` cannot do on its own.",
		authority: "ANL-CHG-001 v0.8 section 11; Analytics.spec.js (the disclosure button toggles with the keyboard's click and names the region it controls)",
	},
];

// Boards that draw the disclosure: every board but the four whose state shows no definitions (31B no records,
// 31D all reads failed, 31G loading, 31H no permitted area; ANL section 10A.11).
const WITH_DISCLOSURE = [
	"21", "21X", "22", "23", "24", "25", "26", "27", "28", "29", "29F", "30", "30B", "31A", "31C", "31E", "31F", "31J",
];

export const DEPARTURES = Object.fromEntries(WITH_DISCLOSURE.map((id) => [`ANL-DES-${id}`, [...DISCLOSURE]]));

DEPARTURES["ANL-DES-31F"].push({
	text: "Supply of printers We could not load the current position.",
	omitsText: ["Supply of printers We could not load the current Award position."],
	path: "outstanding work row for Tender 044 (the sentence)",
	reason:
		"The board and ANL section 10A.11 word the failed stage as \"We could not load the current Award position.\". The server's wording is generic, \"We could not load the current position.\", because the owners do not say which stage failed, so Analytics cannot name Award.",
	authority: "Owner/lead decision 5 October 2026 (the server sends the generic sentence); recorded in docs/mvp-1-r1/19_analytics/reconciliation/page_needs.md",
});

// Boards compared by analytics.fidelity.spec.js: all 22, each mounted on its own captured payload. ANL-DES-21X is the
// Overview payload with the definitions opened; ANL-DES-31G is the loading state (the page's one read stays pending);
// every other board has its own golden payload, which also sets its route.
export const COVERED = [
	"ANL-DES-21", "ANL-DES-21X", "ANL-DES-22", "ANL-DES-23", "ANL-DES-24", "ANL-DES-25", "ANL-DES-26", "ANL-DES-27",
	"ANL-DES-28", "ANL-DES-29", "ANL-DES-29F", "ANL-DES-30", "ANL-DES-30B",
	"ANL-DES-31A", "ANL-DES-31B", "ANL-DES-31C", "ANL-DES-31D", "ANL-DES-31E", "ANL-DES-31F", "ANL-DES-31G", "ANL-DES-31H", "ANL-DES-31J",
];
