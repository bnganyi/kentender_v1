/**
 * Structure Budget & Funding builds that its v1.9 boards do not draw.
 *
 * Same shape as the Planning and Departmental Needs registries: what it is,
 * why it is there, and who decided. Anything not named here fails, and an
 * entry that stops matching fails too, so this file cannot quietly rot.
 *
 * Budget's boards are multi-state: one `.dc.html` carries every state of a
 * screen behind `<sc-if>` blocks, resolved by the spec beside this file. Two
 * consequences worth knowing before adding an entry here:
 *
 *   - Resolve the state the way the board's own switcher does. `showWorkspace`
 *     is false for Loading, No baseline, Forbidden and Server error — each of
 *     those draws ONLY its centred card. Comparing against the default (true)
 *     renders the whole workspace behind the empty panel, which is a state the
 *     design never shows, and every landmark in it then masks a real
 *     difference. Not a departure; a harness mistake.
 *   - Both instruments must read one resolved board. The spec resolves it once
 *     and hands the text gate its words and this gate its markup.
 */
/**
 * The workspace's three *authorised* empty states — no baseline, server error
 * and loading — keep the page header and, in it, the financial-year filter.
 * Forbidden does not, and the board and the live screen agree there: an
 * unauthorised reader gets the lone centred panel and nothing else.
 */
const AUTHORISED_EMPTY_STATE_HEADER = [
	{
		path: "h1",
		because:
			"The board draws each empty state as a lone centred card with no page header, because " +
			"the design tool shows one state at a time and has no year to change. The live workspace " +
			"keeps its header, and the financial-year filter that sits in it, precisely so an officer " +
			"who lands on a year with no allocation — or on a failed load — can move to a year that " +
			"has one. Without it the screen is a dead end. Forbidden deliberately does NOT get this: " +
			"there, board and build agree on the lone panel, and the access spec asserts the filter " +
			"is absent.",
		authority:
			"BUD-CHG-001 v1.9, artboard reconciliation table: \"replaced by a changeable year filter " +
			"on the workspace\" — the requirement contradicts the board and wins (AGENTS.md §6.6)",
	},
];

/**
 * Both History tabs — the budget detail's and the approval task's — are titled
 * in the build and untitled on the board.
 */
const VERSION_HISTORY_CARD_TITLE = [
	{
		path: "card+blueprint > h3",
		because:
			"The board's History tab draws the timeline with no heading over it, leaving the tab " +
			"label to name the section. The requirement calls the same thing a \"Version history " +
			"card\" on both screens, and a card in this design system is titled by a " +
			"`.kt-card-title` — which is what every other tab on both screens does.",
		authority: "BUD-CHG-001 v1.9 §BUD-DES-07A and §BUD-DES-13 — \"Version history card\"",
	},
];

/**
 * Every dialog on every board titles itself with a styled `<div>`; every live
 * dialog uses a real heading carrying the same class.
 */
const DIALOG_TITLE_IS_A_HEADING = [
	{
		path: "dialog > h2",
		because:
			"The board draws `<div class=\"dialog-title\">`; the build renders `<h2 " +
			"class=\"dialog-title\">`. A dialog needs an accessible name, and a heading is how " +
			"one is given — the same reason this instrument treats a region titled by an `h2` and a " +
			"region titled by a styled `div` as different structures. This is that rule pointing the " +
			"other way: the build is MORE structured than the board, not less, and the design tool " +
			"simply has no heading element in its dialog template.",
		authority: "KT-STD-001 §2.5 modal pattern; `.dialog-title` is the design system's own class, which the build carries",
	},
];

export const DEPARTURES = {
	"BudgetWorkspaceScreen#BUD-DES-16-no-baseline": AUTHORISED_EMPTY_STATE_HEADER,
	"BudgetWorkspaceScreen#BUD-DES-16-server-error": AUTHORISED_EMPTY_STATE_HEADER,
	"BudgetApprovalTaskScreen#BUD-DES-08-return-dialog": DIALOG_TITLE_IS_A_HEADING,
	"BudgetClosureScreen#BUD-DES-17": [
		{
			replaces: ["card+blueprint > h2"],
			because:
				"The board draws closure as a SECTION of the Budget detail surface: the page keeps its " +
				"own h1 (the budget) and the closure surface is titled h2 beneath it, with the tabs " +
				"hidden. The build gives closure its own addressable screen at `/<code>/close`, where " +
				"\"Close budget for FY …\" is the page's only title and the budget it belongs to is the " +
				"line under it — so h1 is the correct element for it there. One top-level heading " +
				"either way; the tag follows from which composition is in force.\n\n" +
				"OPEN, and wider than this entry: BUD-CHG-001 v1.9 §BUD19-CHG-011 says closure adds " +
				"\"no new route\" and belongs \"on existing surfaces\". A separate route is what was " +
				"built. Whether that reading is about URLs or about workflow is an owner call, not a " +
				"fidelity fix — folding the screen back into the detail surface would change the route " +
				"contract and the access spec's seven routes. Raised 24 Sep 2026; this entry records " +
				"the heading only, and is superseded the moment that question is answered.",
			authority: "Dated live finding, 24 Sep 2026 — escalated to the owner, not settled",
		},
		{
			path: "dialog",
			replaces: ["card+blueprint > dialog"],
			because:
				"A static artboard cannot portal, so it draws the closure confirmation nested inside " +
				"the card it was opened from. A real modal is rendered at the page root, where it owns " +
				"its own stacking context and is not clipped by an ancestor's overflow. Same container, " +
				"same contents, same order within itself — only its parent differs, and only because " +
				"the board has no way to express an overlay.",
			authority: "KT-STD-001 §2.5 modal pattern; the same convention the Departmental Needs dialogs record",
		},
	],
	"BudgetDetailScreen#BUD-DES-07A-history": VERSION_HISTORY_CARD_TITLE,
	"BudgetApprovalTaskScreen#BUD-DES-13-history": VERSION_HISTORY_CARD_TITLE,
};

/**
 * The screens whose structure is compared against a board. A screen that has a
 * board and is not in this list is not done — the same rule the Planning
 * registry states.
 */
export const COVERED = [
	"BudgetWorkspaceScreen",
	"RegisterAllocationScreen",
	"BudgetVersionEditorScreen",
	"BudgetDetailScreen",
	"BudgetLineDetailScreen",
	"BudgetApprovalTaskScreen",
	"BudgetClosureScreen",
];

/**
 * The label `budget-fidelity.spec.ts` gives a COVERED screen where it names
 * the board variant rather than the component (checked by
 * tests/ui/fidelity/covered.spec.js).
 */
export const COVERED_AS = {
	RegisterAllocationScreen: "BUD-DES-02",
	BudgetVersionEditorScreen: "BUD-DES-03",
	BudgetLineDetailScreen: "BUD-DES-06",
};
