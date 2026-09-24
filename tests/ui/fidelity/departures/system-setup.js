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
export const DEPARTURES = {};

/**
 * Artboards whose built screen is compared and matches. Moved here from
 * REBUILD_QUEUE one by one as each screen is re-ported (plan Phase 5); a
 * screen is not done until it is here.
 */
export const COVERED = [];

/**
 * Artboards not yet built faithfully, recorded 24 Sep 2026 (tracker CFG14-109)
 * as the Phase 5 work queue. Each is still compared: a queued artboard whose
 * build now matches FAILS, so the entry has to be moved to COVERED rather than
 * left to rot. The value says why it is queued.
 */
const REPORT = "structure differs from the board (recorded by the Phase 1 red run)";
const UNMOUNTABLE = "no component renders this state from props yet; Phase 5 builds it";
export const REBUILD_QUEUE = {
	"C01#configured": REPORT,
	"C01#first-run": REPORT,
	"C01#conflict": UNMOUNTABLE,
	"C01#missing-authority": UNMOUNTABLE,
	"C02#overview": UNMOUNTABLE,
	"C02#overview-disabled": UNMOUNTABLE,
	"C02#narrow": UNMOUNTABLE,
	"C02#empty": UNMOUNTABLE,
	"C02#add-year": REPORT,
	"C02#detail": UNMOUNTABLE,
	"C02#detail-row-variants": UNMOUNTABLE,
	"C02#disable": UNMOUNTABLE,
	"C02#forms": UNMOUNTABLE,
	"C02#form-states": UNMOUNTABLE,
	"C03A#list": UNMOUNTABLE,
	"C03A#add": REPORT,
	"C03A#edit": REPORT,
	"C03A#disabled": UNMOUNTABLE,
	"C03A#duplicate": UNMOUNTABLE,
	"C03A#empty": UNMOUNTABLE,
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
