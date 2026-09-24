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
	"C03BC#list": UNMOUNTABLE,
	"C03BC#detail": UNMOUNTABLE,
	"C03BC#rename": UNMOUNTABLE,
	"C03BC#add": UNMOUNTABLE,
	"C03BC#kinds": UNMOUNTABLE,
	"C03BC#version": UNMOUNTABLE,
	"C03BC#states": UNMOUNTABLE,
	"C03D#pending": UNMOUNTABLE,
	"C03D#verified": UNMOUNTABLE,
	"C03D#rejected": UNMOUNTABLE,
	"C03D#history": UNMOUNTABLE,
	"C03D#evidence": UNMOUNTABLE,
	"C04#list": UNMOUNTABLE,
	"C04#detail": UNMOUNTABLE,
	"C04#add": UNMOUNTABLE,
	"C04#calendar": UNMOUNTABLE,
	"C04#calendar-detail": UNMOUNTABLE,
	"C04#calendar-version": UNMOUNTABLE,
	"C04#calendar-history": UNMOUNTABLE,
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
	"C04#calendar": "the board's Holidays table and heading (added 24 Sep 2026) are not built",
	"C04#detail": "the interval table's Minimum days / Maximum days columns (board refresh) are not built",
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
