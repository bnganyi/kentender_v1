/**
 * Structure System setup builds that its CFG-CHG-002 v0.14 boards do not draw,
 * and the screens that already match them.
 *
 * Same shape as the other modules' registries: what it is, why it is there,
 * who decided. Anything not named here fails, and an entry that stops matching
 * fails too.
 *
 * Keys are `Board#artboard`, e.g. `C01#configured` for `#configured` in
 * `C01-Procuring-Entity.dc.html`. System setup's boards address each state by
 * an element id rather than a `<section>`, so the key names the board and the
 * id, not a component.
 */
const SAVED_NOTICE_IS_A_LATER_STATE = {
	omits: ["notice.is-live"],
	because:
		"The board draws the 'Site details saved' / 'Site configured' notice under the form as the state after a save. " +
		"The screen shows it only after one; tabs/ProcuringEntityTab.spec.js asserts it in that state.",
	authority: "CFG-CHG-002 v0.14 §10.2 (saved notice); KT-STD-001 §3 (states are distinct)",
};

const DIALOG_TITLE_REASON = {
	because:
		"The board titles a dialog with a styled <div class=\"dialog-title\">; the build uses <h2 class=\"kt-dialog-title\"> " +
		"so the dialog has an accessible name — more structure than the board, not less (Budget records the same).",
	authority: "KT-STD-001 §3 (dialog focus and naming); design system's own .kt-dialog-title",
};
// The component harness roots the skeleton above the dialog; the browser
// gate scopes to the dialog itself, where the title's path is just "h2".
const DIALOG_TITLE_IS_A_HEADING = [
	{ path: "dialog > h2", ...DIALOG_TITLE_REASON },
	{ path: "h2", ...DIALOG_TITLE_REASON },
];

export const DEPARTURES = {
	"C02#overview": [
		{
			path: "card",
			because:
				"One card per year: the narrow-width composition (§10.3, board #narrow), rendered beside the table and shown only " +
				"below 700px; compared on its own as C02#narrow.",
			authority: "CFG-CHG-002 v0.14 §10.3 narrow-width composition",
		},
	],
	"C02#add-year": DIALOG_TITLE_IS_A_HEADING,
	"C02#disable": DIALOG_TITLE_IS_A_HEADING,
	"C03A#add": DIALOG_TITLE_IS_A_HEADING,
	"C03BC#rename": DIALOG_TITLE_IS_A_HEADING,
	"C04#detail": [
		{
			omits: ["field"],
			because:
				"The board draws the selected-interval editor on the saved detail. A saved version is read-only, so those " +
				"controls live in the schedule editor (new version / correction), not here.",
			authority: "CFG-CHG-002 v0.14 §4.6 (versions are immutable), §10.9 (selected interval editor)",
		},
	],
	"C03BC#version": [
		{
			omits: ["notice.is-critical"],
			because:
				"The board draws the live-data impact warning as a variant beside the ordinary warning. It shows only when the " +
				"version being replaced is marked valid (the server's blocks-new-use fact); the component spec proves it there.",
			authority: "CFG-CHG-002 v0.14 §10.6 (live-data impact variant)",
		},
	],
	"C03BC#add": [
		{
			testid: "kt-rule-kind-fields",
			because:
				"The spec places the selected kind's groups between Rule kind and the common fields; the board draws those " +
				"groups separately as #kinds cards, each compared on its own (C03BC#kinds~…).",
			authority: "CFG-CHG-002 v0.14 §10.6 (add-rule form order), §10.7",
		},
	],
	"C03BC#detail": [
		{
			testid: "kt-procset-rule-readonly",
			because:
				"The board's saved-detail specimen is still correctable. A version that can no longer be corrected in place " +
				"shows the board's own read-only state (#states card 1) above its groups.",
			authority: "CFG-CHG-002 v0.14 §8.1, §10.6 (C03BC #states)",
		},
		{
			testid: "kt-procset-rule-values",
			because:
				"The board's saved detail is the pending specimen, with no values yet. A saved rule shows what it says: a " +
				"method rule's conditions and a reference rule's typed rows, as tables inside Rule details (never raw JSON).",
			authority: "CFG-CHG-002 v0.14 §10.7 (no JSON editor; typed rows); KT-STD-001 §3 (a record shows its content)",
		},
	],
	"C03A#edit": DIALOG_TITLE_IS_A_HEADING,
	"C01#configured": [SAVED_NOTICE_IS_A_LATER_STATE],
	"C01#first-run": [
		SAVED_NOTICE_IS_A_LATER_STATE,
		{
			omits: ["tabs"],
			because:
				"The first-run board repeats the page's tab bar inside the artboard to show the other four tabs disabled. " +
				"The live tab bar is the page header's own (SystemSetup.vue), compared with the header, and its disabled " +
				"state is proved by system-setup-worlds.spec.ts.",
			authority: "CFG-CHG-002 v0.14 §9 (one shell, five tabs) / §10.2 (first run disables the other four tabs)",
		},
	],
};

/**
 * Artboards whose built screen is compared and matches. Moved here from
 * REBUILD_QUEUE one by one as each screen is re-ported (plan Phase 5); a
 * screen is not done until it is here.
 */
/**
 * Specimen artboards: the board draws only a fragment of the screen (the
 * fields a state concerns and its notice). Every container the fragment
 * draws must be present, in order; the rest of the screen is not the
 * specimen's business, so additions are not reported. Shared by the
 * component and browser specs.
 */
export const FRAGMENTS = [
	"C01#conflict",
	"C01#missing-authority",
	"C02#overview-disabled",
	"C02#empty",
	"C02#detail-row-variants",
	"C03BC#version",
	"C03D#verified",
	"C03D#rejected",
];

export const COVERED = [
	// 5A Procuring entity — 24 Sep 2026
	"C01#configured",
	"C01#first-run",
	"C01#conflict",
	"C01#missing-authority",
	// 5B Financial years — 24 Sep 2026
	"C02#overview",
	"C02#overview-disabled",
	"C02#narrow",
	"C02#empty",
	"C02#add-year",
	"C02#detail",
	"C02#detail-row-variants",
	"C02#disable",
	"C02#forms",
	"C02#form-states",
	// 5C Funding sources — 24 Sep 2026
	"C03A#list",
	"C03A#add",
	"C03A#edit",
	"C03A#disabled",
	"C03A#duplicate",
	"C03A#empty",
	// 5D Procurement rules, first half — 24 Sep 2026
	"C03BC#list",
	"C03BC#list~empty",
	"C03BC#list~no-version",
	"C03BC#list~not-published",
	"C03BC#detail",
	"C03BC#rename",
	// 5D second half — 24 Sep 2026
	"C03BC#list~partial",
	"C03BC#add",
	"C03BC#kinds~reservation",
	"C03BC#kinds~exclusive",
	"C03BC#kinds~margins",
	"C03BC#kinds~price-index",
	"C03BC#kinds~approval",
	"C03BC#kinds~publication",
	"C03BC#version",
	"C03BC#states~read-only",
	"C03BC#states~overlap",
	"C03BC#states~stale",
	// 5E Source checks — 24 Sep 2026
	"C03D#pending",
	"C03D#verified",
	"C03D#rejected",
	"C03D#history",
	// 5F Schedules and calendars, first half — 24 Sep 2026
	"C04#list",
	"C04#list~empty",
	"C04#detail",
	"C04#calendar~working-days",
	"C04#calendar~editor",
	"C04#calendar-detail",
	"C04#calendar-version",
	"C04#calendar-history",
	// 5F second half — 24 Sep 2026
	"C04#add~identity",
	"C04#add~version-footer",
	"C04#detail~selected-interval",
];

/**
 * Artboards not yet built faithfully, recorded 24 Sep 2026 (tracker CFG14-109)
 * as the Phase 5 work queue. Each is still compared: a queued artboard whose
 * build now matches FAILS, so the entry has to be moved to COVERED rather than
 * left to rot. The value says why it is queued.
 */
const REPORT = "structure differs from the board (recorded by the Phase 1 red run)";
const UNMOUNTABLE = "no component renders this state from props yet; Phase 5 builds it";
export const REBUILD_QUEUE = {
	"C03BC#kinds~method":
		"D21 (owner, 24 Sep 2026): Method eligibility keeps its built model and full editor; the board's value-range " +
		"statuses and fact/comparison condition rows need a model change. Its new-version top is compared as #version.",
	"C03BC#states~no-coverage":
		"No setup screen decides coverage for a required date yet; that is the resolver's answer to a consumer (FU-28).",
	"C03D#evidence":
		"Decision-time vs current source check belongs to a consuming record's evidence detail, which no setup screen " +
		"shows yet (FU-30).",
	"Reminders#unchanged": REPORT,
	"Reminders#edited": UNMOUNTABLE,
	"Reminders#zero": UNMOUNTABLE,
	"Reminders#invalid": UNMOUNTABLE,
	"Common#loading": UNMOUNTABLE,
	"Common#denied": UNMOUNTABLE,
	"Common#load-error": UNMOUNTABLE,
};

/**
 * States whose refreshed board carries WORDS the live screen lacks, found by
 * the browser landmark gate on 24 Sep 2026. Same rot rule as the queue: an
 * entry whose words now match fails until it is removed.
 */
export const LANDMARK_DRIFT = {
	// Emptied by 5F (24 Sep 2026): the calendar's Holidays heading and the
	// interval table's Minimum/Maximum days columns are built.
};

/**
 * States whose words depend on the shared dev site's current data rather than
 * on the screen, so they can neither be required to match nor required to
 * differ. Their text comparison is skipped until the Phase 4 CONFIG fixture
 * world pins the data (tracker CFG14-401), which removes every entry here.
 * Their structural comparison still runs.
 */
export const FIXTURE_PENDING = {
	// Emptied 24 Sep 2026 (tracker CFG14-401): C02 detail now runs on the
	// CONFIG world (make ui-system-setup-fidelity-gate builds it first).
}
