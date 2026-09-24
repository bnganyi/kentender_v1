import { test, expect, Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import { compareSkeletons, formatMismatch, skeletonOf } from "../../fidelity/skeleton.js";
import { DEPARTURES, FIXTURE_PENDING, FRAGMENTS, LANDMARK_DRIFT, REBUILD_QUEUE } from "../../fidelity/departures/system-setup.js";
import { JSDOM } from "jsdom";
import {
	openArtboard,
	landmarks,
	expectLandmarkSubsequence,
	collectPageErrors,
	outerHtml,
	expectLayoutSanity,
} from "../../helpers/designFidelity";

/**
 * System setup design-fidelity gate (AGENTS.md §6.6 enforcement).
 *
 * For every System setup screen with a `.dc.html` artboard, this spec renders
 * the artboard itself and derives the expectations from that render:
 *
 *   - the artboard's ordered landmark TEXTS must appear in order in the live
 *     page (the landmark gate), and
 *   - the containers the artboard draws, and how they nest, must be the ones
 *     the live tab body is built from (`expectBoardStructure`, the same
 *     comparator as `ui-structure-gate`). Boards not yet re-ported are listed
 *     in REBUILD_QUEUE and must still differ.
 *
 * Geometry is NOT measured: the probes in designFidelity.ts have no call
 * sites (AGENTS.md §6.6).
 *
 * Scope: the boards this module owns — C01, C02, C03A, C03BC, C03D, C04 and
 * Reminders. The AUTH-owned boards were removed from this folder by their
 * owner and their tests with them (plan D2, FOLLOW_UPS FU-11): CFG cannot
 * assert fidelity against artboards it does not own. The AUTH tabs still
 * render inside this page; their behaviour is covered by the responsibility
 * and access specs, not here.
 *
 * Prerequisite state: the KT-STD §8 seed world
 * (`bench execute kentender_core.seeds.site_setup.run` — idempotent; the
 * `ui-system-setup-fidelity-gate` make target runs it first).
 *
 * Known, deliberate deltas NOT asserted here, each explained at its own test:
 * record ids, names and dates (the seed's business, not this gate's); a
 * board's sampled subset or ordering of a closed vocabulary; and the action
 * sets a board documents for several states at once, which are asserted in
 * the state each actually belongs to.
 */

const DESIGN_DIR = "docs/mvp-1-r1/09_unified_system_setup/design";
const LIVE_SCOPE = ".kt-setup-shell";
const DIALOG_SCOPE = ".kt-dialog";
// The focused open/close/deadline form is an inline panel in the year detail (D18).
const FORM_SCOPE = '[data-testid="kt-fy-intake"]';
// The tab body: the board's artboard is the content under the shared header
// and tabs, so the header is compared once on its own, not in every state.
const PANEL_SCOPE = ".kt-setup-panel";

/**
 * The structural half (tests/ui/fidelity/skeleton.js), keyed like the
 * component spec. A board state still in REBUILD_QUEUE must still DIFFER —
 * so fixing a screen forces its move to COVERED instead of leaving the queue
 * to rot; any other state must match.
 */
/**
 * The landmark (text-order) half. Strict, except for the few states whose
 * refreshed board carries words the live screen does not have yet
 * (LANDMARK_DRIFT); those must still differ, so the entry is removed the
 * moment the screen is re-ported.
 */
function expectBoardLandmarks(wanted: string[], live: string[], label: string, key: string, ...rest: unknown[]): void {
	const check = () => (expectLandmarkSubsequence as (...args: unknown[]) => void)(wanted, live, label, ...rest);
	// Data-dependent until the CONFIG fixture world exists (FIXTURE_PENDING).
	if ((FIXTURE_PENDING as Record<string, string>)[key]) return;
	if (!(LANDMARK_DRIFT as Record<string, string>)[key]) return check();
	expect(check, `${key} words now match its board — remove it from LANDMARK_DRIFT`).toThrow();
}

async function expectBoardStructure(page: Page, liveScope: string, art: Page, artScope: string, key: string): Promise<void> {
	const liveHtml = await outerHtml(page, liveScope);
	const artHtml = await outerHtml(art, artScope);
	expect(liveHtml, `${key}: live scope ${liveScope} not found`).not.toBe("");
	expect(artHtml, `${key}: board scope ${artScope} not found`).not.toBe("");
	const root = (html: string) => new JSDOM(`<body>${html}</body>`).window.document.body.firstElementChild!;
	const result = compareSkeletons(skeletonOf(root(artHtml)), skeletonOf(root(liveHtml)), {
		departures: ((DEPARTURES as Record<string, unknown[]>)[key] || []) as never[],
	});
	// A specimen board draws a fragment of the screen (FRAGMENTS).
	if ((FRAGMENTS as string[]).includes(key)) result.extra = [];
	const message = formatMismatch(key, result);
	if ((REBUILD_QUEUE as Record<string, string>)[key]) {
		expect(message, `${key} now matches its board — move it from REBUILD_QUEUE to COVERED`).not.toBe("");
	} else {
		expect(message, message).toBe("");
	}
}

test.use({ viewport: { width: 1600, height: 1024 } });

async function openSetupTab(page: Page, tab: string, readySelector: string): Promise<string[]> {
	const errors = collectPageErrors(page);
	await page.goto(`/app/system-setup#${tab}`, { waitUntil: "domcontentloaded" });
	await page.waitForSelector(readySelector, { timeout: 20_000 });
	// Geometry probes measure text: the web fonts must be applied, or the
	// fallback face's different metrics make truncation checks flaky.
	await page.evaluate(() => (document as any).fonts?.ready?.catch(() => undefined));
	return errors;
}

/**
 * The reservation rule's current version id, read from the server rather than
 * hardcoded: version ids are hashes under the v0.11 envelope, and the seed's
 * version number moves as fixtures run.
 */
async function currentReservationVersion(page: Page): Promise<string> {
	const response = await page.request.get(
		"/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings"
	);
	const body = await response.json();
	const set = (body.message?.reference_sets || []).find(
		(row: any) => row.reference_kind === "Reservation rules"
	);
	expect(set?.version?.name, "a current Reservation rules version").toBeTruthy();
	return set.version.name;
}

/** The first registered working-day calendar, or "" when none exists yet. */
async function firstCalendar(page: Page): Promise<string> {
	const response = await page.request.get(
		"/api/method/kentender_core.api.procurement_settings_api.get_procurement_settings"
	);
	const body = await response.json();
	return (body.message?.calendars || [])[0]?.calendar || "";
}

test.describe("System setup — design fidelity", () => {
	// CFG-CHG-002 v0.11 §10.2 — C01-Procuring-Entity.dc.html's own anchored
	// sections (#configured/#conflict) are the fidelity source, replacing
	// the retired Planning-owned C01-C04-Setup.dc.html frame (plan D-port,
	// Phase 3A). "Setup record" and "Plan approval authority" are new
	// sections in v0.11; the county flag is now an explicit Yes/No radio,
	// never a checkbox.
	test("C01-configured — Procuring entity tab with route, county radio, setup record and approval readiness", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#configured";
		await openArtboard(art, `${DESIGN_DIR}/C01-Procuring-Entity.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procuring-entity", '[data-testid="kt-setup-pe-record"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C01-configured", "C01#configured");
		await expectBoardStructure(page, PANEL_SCOPE, art, scope, "C01#configured");
		expect(await page.locator('[data-testid="kt-setup-pe-route"] option').allTextContents()).toEqual([
			"Cabinet Secretary",
			"County Executive Committee Member",
			"Board of Directors",
			"Council",
		]);
		expect(await page.locator('[data-testid="kt-setup-pe-county-yes"]').isVisible()).toBe(true);
		expect(await page.locator('[data-testid="kt-setup-pe-county-no"]').isVisible()).toBe(true);
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C01-conflict — county applicability mismatch shown as a critical notice, nothing saved", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#conflict";
		await openArtboard(art, `${DESIGN_DIR}/C01-Procuring-Entity.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procuring-entity", '[data-testid="kt-setup-pe-record"]');
		const typeBefore = await page.locator('[data-testid="kt-setup-pe-type"]').inputValue();
		await page.selectOption('[data-testid="kt-setup-pe-type"]', "County Government");
		// The current record is a non-county entity (No is checked); leave it
		// as-is so the type/county combination genuinely conflicts.
		await page.click('[data-testid="kt-setup-pe-submit"]');
		await page.waitForSelector('[data-testid="kt-setup-pe-county-conflict"]');
		expect(await page.locator('[data-testid="kt-setup-pe-county-conflict"]').textContent()).toBe(
			"Conflict. The county answer does not match the entity details."
		);
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C01-conflict", "C01#conflict");
		await expectBoardStructure(page, PANEL_SCOPE, art, scope, "C01#conflict");
		// Refused before save: a reload shows the unchanged record.
		await page.reload({ waitUntil: "domcontentloaded" });
		await page.waitForSelector('[data-testid="kt-setup-pe-record"]');
		expect(await page.locator('[data-testid="kt-setup-pe-type"]').inputValue()).toBe(typeBefore);
		// The refusal itself is the one expected console line: Frappe echoes
		// the server's ConfigurationError traceback for the 417 response in
		// developer mode. Nothing else may be logged.
		expect(
			errors.filter((e) => !e.includes("The county answer does not match") && !/status of 417/.test(e)),
			"console errors"
		).toEqual([]);
		await art.close();
	});

	// CFG-CHG-002 v0.11 §10.3 — C02-Financial-Years.dc.html's own anchored
	// sections replace the retired Planning-owned C02/C02-close frames and
	// the CFG-DES-04/05 standalone dialog boards (Phase 3B, FU-11). The
	// overview now carries all three intake activities and links to a
	// per-year Submission periods detail; every open/close/deadline action
	// lives on that detail.
	//
	// One deliberate, documented delta: the artboard's table cells pluralise
	// two activity names ("Departmental plans", "Disposal plans") while its
	// own dialog titles use the singular §8 vocabulary ("Open departmental
	// plan submissions"). The live screen uses the §8 singular throughout so
	// the table, the dialogs, the blockers and the server-composed change
	// history read as one vocabulary; those two `th` landmarks are dropped
	// from the comparison rather than silently passed (FOLLOW_UPS FU-12).
	const C02_PLURAL_ACTIVITY_HEADERS = ["Departmental plans", "Disposal plans"];

	test("C02-overview — Financial years list with all three intake activities", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#overview";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = (await landmarks(art, scope)).filter((text) => !C02_PLURAL_ACTIVITY_HEADERS.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years", '[data-testid="kt-fy-table"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C02-overview", "C02#overview");
		await expectBoardStructure(page, PANEL_SCOPE, art, scope, "C02#overview");
		// The third activity is the v0.11 addition; the row action is the link
		// to that year's own submission periods, never an inline open/close.
		await expect(page.locator('[data-testid="kt-fy-disposal_plan-2027-2028"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-fy-detail-2027-2028"]')).toHaveText("Submission periods");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-detail — Submission periods for one year, with the change-history disclosure", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#detail";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = (await landmarks(art, scope)).filter((text) => !C02_PLURAL_ACTIVITY_HEADERS.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years/2027-2028", '[data-testid="kt-setup-fy-detail-card"]');
		// The artboard draws the history table expanded; the live disclosure
		// starts collapsed, so open it before comparing landmarks.
		await page.click('[data-testid="kt-fy-history-toggle"]');
		await page.waitForSelector('[data-testid="kt-fy-history-body"] table');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C02-detail", "C02#detail");
		await expectBoardStructure(page, PANEL_SCOPE, art, scope, "C02#detail");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-add-year — Add financial year dialog with the server preview", async ({ page, browser }) => {
		const art = await browser.newPage();
		// `document.querySelector` takes the first match: the dialog itself,
		// not the duplicate/Company defect notices beside it in the grid.
		const scope = "#add-year .dialog";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years", '[data-testid="kt-fy-table"]');
		await page.click('[data-testid="kt-fy-add-open"]');
		await page.waitForSelector('[data-testid="kt-fy-add"]');
		// Reach the artboard's state: a start year entered, server preview shown.
		await page.fill('[data-testid="kt-fy-start-year"]', "2035");
		await page.waitForSelector('[data-testid="kt-fy-preview"]', { timeout: 10_000 });
		expectBoardLandmarks(wanted, await landmarks(page, DIALOG_SCOPE), "C02-add-year", "C02#add-year");
		await expectBoardStructure(page, DIALOG_SCOPE, art, scope, "C02#add-year");
		await expectLayoutSanity(page, "C02#add-year editor");

		// The exact duplicate defect, and Add disabled with it (CFG-UX-AC-05).
		// The Company defect shares that treatment and is proven server-side in
		// kentender_core.tests.test_site_configuration.
		await page.fill('[data-testid="kt-fy-start-year"]', "2027");
		await page.waitForSelector('[data-testid="kt-fy-duplicate"]');
		await expect(page.locator('[data-testid="kt-fy-duplicate"]')).toHaveText(
			"Duplicate. This financial year already exists.View financial year"
		);
		await expect(page.locator('[data-testid="kt-fy-add-confirm"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-open-form — Open submissions form with the cross-year replacement notice", async ({ page, browser }) => {
		const art = await browser.newPage();
		// Third card in the forms grid: Open · Departmental plans, the one that
		// draws the cross-year replacement notice.
		const scope = "#forms .card:nth-child(3)";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years/2026-2027", '[data-testid="kt-setup-fy-detail-card"]');
		// CONFIG world: 2027/28 holds departmental plans, so opening them for
		// 2026/27 shows the replacement notice. Nothing is submitted.
		await page.click('[data-testid="kt-fy-open-dpp"]');
		await page.waitForSelector('[data-testid="kt-fy-intake-replaces"]');
		expectBoardLandmarks(wanted, await landmarks(page, FORM_SCOPE), "C02-open-form", "C02#forms");
		await expectBoardStructure(page, FORM_SCOPE, art, scope, "C02#forms");
		await expectLayoutSanity(page, "C02#forms editor");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-deadline-form — Change closing time form", async ({ page, browser }) => {
		const art = await browser.newPage();
		// Seventh card in the forms grid: the deadline edit.
		const scope = "#forms .card:nth-child(7)";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years/2027-2028", '[data-testid="kt-setup-fy-detail-card"]');
		await page.click('[data-testid="kt-fy-deadline-needs"]');
		await page.waitForSelector('[data-testid="kt-fy-intake"][data-mode="deadline"]');
		expectBoardLandmarks(wanted, await landmarks(page, FORM_SCOPE), "C02-deadline-form", "C02#forms");
		await expectBoardStructure(page, FORM_SCOPE, art, scope, "C02#forms");
		await expectLayoutSanity(page, "C02#forms editor");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-disable — the blocked disable dialog names its exact blockers", async ({ page, browser }) => {
		const art = await browser.newPage();
		// First dialog in the disable grid: "This financial year cannot be disabled".
		const scope = "#disable .dialog";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years/2027-2028", '[data-testid="kt-setup-fy-detail-card"]');
		await page.click('[data-testid="kt-fy-disable-open"]');
		await page.waitForSelector('[data-testid="kt-fy-disable"]');
		expectBoardLandmarks(wanted, await landmarks(page, DIALOG_SCOPE), "C02-disable", "C02#disable");
		await expectBoardStructure(page, DIALOG_SCOPE, art, scope, "C02#disable");
		await expect(page.locator('[data-testid="kt-fy-disable-blocker"]').first()).toHaveText(
			"Departmental needs submissions are still open."
		);
		await expect(page.locator('[data-testid="kt-fy-disable-confirm"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// CFG-CHG-002 v0.14 §10.5 — C03A-Funding-Sources.dc.html (tracker
	// CFG14-5C): the list against #list, the add dialog against #add. The
	// edit, disabled, duplicate and empty artboards are compared by the
	// component structure gate.
	test("C03A-list — Funding sources list with the availability column", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#list";
		await openArtboard(art, `${DESIGN_DIR}/C03A-Funding-Sources.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings", '[data-testid="kt-procset-sources"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C03A-list", "C03A#list");
		await expectBoardStructure(page, '[data-testid="kt-procset-sources"]', art, scope, "C03A#list");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03A-editor — the availability choice states what it governs, and a duplicate name is refused before submit", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#add";
		await openArtboard(art, `${DESIGN_DIR}/C03A-Funding-Sources.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/funding-sources/new", '[data-testid="kt-procset-source-editor"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C03A-editor", "C03A#add");
		await expectBoardStructure(page, DIALOG_SCOPE, art, scope, "C03A#add");
		await expectLayoutSanity(page, "C03A#add editor");

		await page.fill('[data-testid="kt-fs-name"]', "Government of Kenya");
		await page.waitForSelector('[data-testid="kt-fs-duplicate"]');
		await expect(page.locator('[data-testid="kt-fs-duplicate"]')).toHaveText(
			"Duplicate. A funding source with this name already exists."
		);
		await expect(page.locator('[data-testid="kt-fs-save"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// CFG-CHG-002 v0.11 §10.6–§10.9 — the rule editor, the source check and
	// the working-day calendar (Phases 3D–3F). Each renders its own anchored
	// section of the owning artboard.
	test("C03B-add — Add procurement rule offers exactly the seven kinds", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#add";
		await openArtboard(art, `${DESIGN_DIR}/C03BC-Procurement-Rules.dc.html`, scope);
		// The board samples three entity types in its own order; the live control
		// offers the complete closed set in the same canonical order the
		// Procuring entity screen uses. The sample is fixture data, not an
		// ordering contract, so the three labels are excluded — the control's
		// presence is still asserted through the "Entity types" group label.
		const ENTITY_TYPE_SAMPLES = ["National Government Ministry", "County Government", "State Corporation"];
		const wanted = (await landmarks(art, scope)).filter((text) => !ENTITY_TYPE_SAMPLES.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/procurement-rules/new", '[data-testid="kt-procset-rule-editor"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C03B-add", "C03BC#add");
		await expectBoardStructure(page, '[data-testid="kt-procset-rule-editor"]', art, "#add > div", "C03BC#add");
		await expectLayoutSanity(page, "C03BC#add editor");
		expect(await page.locator('[data-testid="kt-rule-kind"] option').allTextContents()).toEqual([
			"Method eligibility",
			"Reservation rules",
			"Exclusive preference",
			"Preference margins",
			"Market price index",
			"Approval applicability",
			"Publication obligations",
		]);
		// Method eligibility keeps its own editor (D21): picking a method that
		// already has a rule points to its new version instead of a duplicate.
		await page.selectOption('[data-testid="kt-rule-kind"]', "Method eligibility");
		await page.selectOption('[data-testid="kt-rule-method"]', "Open Tender");
		await expect(page.locator('[data-testid="kt-rule-method-exists"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-rule-save"]')).toHaveCount(0);
		// Each other kind brings its own validated field group.
		await page.selectOption('[data-testid="kt-rule-kind"]', "Publication obligations");
		await expect(page.locator('[data-testid="kt-po-id"]')).toBeVisible();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03D-pending — Check sources fixes its target and refuses a verified result without evidence", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#pending";
		await openArtboard(art, `${DESIGN_DIR}/C03D-Source-Checks.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const reference = await currentReservationVersion(page);
		const errors = await openSetupTab(
			page,
			`procurement-settings/procurement-rules/${reference}/check-sources`,
			'[data-testid="kt-source-check-rule"]'
		);
		// The board's pending specimen has its unresolved point written.
		await page.fill('[data-testid="kt-sc-unresolved"]', "The applicable amended source and interpretation have not been established.");
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C03D-pending", "C03D#pending");
		await expectBoardStructure(page, '[data-testid="kt-source-check-form"]', art, "#pending > div", "C03D#pending");
		await expectBoardStructure(page, '[data-testid="kt-source-check-history"]', art, "#history > div", "C03D#history");
		await expectLayoutSanity(page, "C03D#pending editor");

		await page.selectOption('[data-testid="kt-sc-result"]', "Verified");
		await expect(page.locator('[data-testid="kt-sc-evidence-required"]')).toHaveText(
			"Complete the source, applicability and interpretation evidence before recording a verified source check."
		);
		await expect(page.locator('[data-testid="kt-sc-record"]')).toBeDisabled();
		// Nothing is recorded: both histories are read-only here.
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C04-calendar — the working-day calendar editor, with row controls only while unsaved", async ({ page, browser }) => {
		const art = await browser.newPage();
		// `#calendar` scopes to the whole missing/add/detail group; its own
		// blueprint header now wraps both the "missing" notice and the
		// calendar editor as plain sibling blocks (no distinguishing class
		// since the C03/C04 header refresh), so the editor — always the last
		// of the three direct children — is selected positionally.
		// The editor is the second of #calendar's two blocks (the first is a
		// schedule's working-days notice, compared in the component gate).
		const scope = "#calendar > div:nth-child(2)";
		await openArtboard(art, `${DESIGN_DIR}/C04-Schedules-Calendars.dc.html`, scope);
		// This one board documents both states at once: the unsaved editor
		// (Cancel / Save calendar version, Add row) and the saved detail
		// (Create new version / Check sources / View usage and history). A
		// live screen is only ever in one of them, so each set of actions is
		// asserted in the state it belongs to rather than both at once.
		const SAVED_ONLY = ["Create new version", "Check sources", "View usage and history"];
		const wanted = (await landmarks(art, scope)).filter((text) => !SAVED_ONLY.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/calendars/new", '[data-testid="kt-procset-calendar"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C04-calendar", "C04#calendar");
		await expectBoardStructure(page, '[data-testid="kt-calendar-editor"]', art, scope, "C04#calendar~editor");
		await expectLayoutSanity(page, "C04#calendar editor");
		await expect(page.locator('[data-testid="kt-cal-weekend-Saturday"]')).toBeChecked();
		await expect(page.locator('[data-testid="kt-cal-weekend-Sunday"]')).toBeChecked();
		await expect(page.locator('[data-testid="kt-cal-add-holiday"]')).toBeVisible();

		// The saved state: read-only, no row controls, and the successor action.
		const calendar = await firstCalendar(page);
		if (calendar) {
			await page.goto(`/app/system-setup#procurement-settings/calendars/${calendar}`, { waitUntil: "domcontentloaded" });
			await page.waitForSelector('[data-testid="kt-cal-name-ro"]', { timeout: 20_000 });
			await expect(page.locator('[data-testid="kt-cal-new-version"]')).toBeVisible();
			await expectBoardStructure(page, '[data-testid="kt-calendar-detail"]', art, "#calendar-detail > div", "C04#calendar-detail");
			await expect(page.locator('[data-testid="kt-cal-add-holiday"]')).toHaveCount(0);
		}
		// Nothing is saved: a calendar version is immutable once written.
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// CFG-CHG-002 v0.11 §10.10 — Reminders.dc.html (Phase 3G). The board's
	// own blueprint header now wraps all four documented states (the C03/C04
	// header refresh), so the first nested `.blueprint` — the unchanged
	// specimen — is what scopes this one state.
	test("Reminders — the threshold states what it sets, its unit and that it is not a deadline", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#unchanged";
		await openArtboard(art, `${DESIGN_DIR}/Reminders.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/reminders", '[data-testid="kt-procset-reminder"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "Reminders", "Reminders#unchanged");
		await expectBoardStructure(page, PANEL_SCOPE, art, scope, "Reminders#unchanged");
		const card = page.locator('[data-testid="kt-procset-reminder"]');
		await expect(card).toContainText("Unit: Calendar days");
		await expect(card).toContainText("This changes reminder timing, not procurement deadlines.");
		await expect(card).toContainText("Use 0 to begin reminders on the milestone date; overdue reminders still apply.");

		// 0–365 is the rule, stated before the round trip (the server refuses
		// the same range — kentender_core.tests.test_procurement_settings).
		await page.fill('[data-testid="kt-reminder-days"]', "366");
		await expect(page.locator('[data-testid="kt-reminder-range-error"]')).toHaveText(
			"Enter a whole number from 0 to 365."
		);
		await expect(page.locator('[data-testid="kt-reminder-save"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// C03BC "#version" (§4.6/§10.6) — correcting a method eligibility rule.
	// The board draws the replacement and its effect; the live screen draws
	// them around the whole rule, because every part of it is editable here
	// and the record that comes out is a new immutable Version.
	test("C03B-version — the Method eligibility editor states the replacement and its effect", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#version";
		await openArtboard(art, `${DESIGN_DIR}/C03BC-Procurement-Rules.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(
			page,
			"procurement-settings/procurement-rules/MPR-OPEN-TENDER-V1/new-version",
			'[data-testid="kt-procset-method-editor"]'
		);
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C03B-version", "C03BC#version");
		// A fragment comparison: the board draws the version form's top and
		// footer; the editable groups sit between them (FRAGMENTS).
		await expectBoardStructure(page, '[data-testid="kt-mve-card"]', art, "#version > div", "C03BC#version");
		await expectLayoutSanity(page, "C03BC#version editor");
		// The board's "Unsaved changes" tag is the state this screen opens in.
		await expect(page.locator('[data-testid="kt-rule-unsaved"]')).toHaveText("Unsaved changes");
		// It opens on the Version it corrects, with every condition editable.
		await expect(page.locator('[data-testid="kt-mve-id-0"]')).toHaveValue("G-VALUE");
		await expect(page.locator('[data-testid="kt-mve-save"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// Retargeted from the retired Planning board to CFG's own C03BC "#detail"
	// (Phase 3D). The saved detail states its groups and its actions; nothing
	// on it is editable, because a correction is a new version (§11.6).
	test("C03BC-list — the rules list with Source check and Details as separate columns", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#list > div:first-child";
		await openArtboard(art, `${DESIGN_DIR}/C03BC-Procurement-Rules.dc.html`, "#list");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/procurement-rules", '[data-testid="kt-procset-rules"]');
		expectBoardLandmarks(wanted, await landmarks(page, '[data-testid="kt-procset-rules"]'), "C03BC-list", "C03BC#list");
		await expectBoardStructure(page, '[data-testid="kt-procset-rules"]', art, scope, "C03BC#list");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03B-detail — a saved rule Version, read-only", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#detail > div";
		await openArtboard(art, `${DESIGN_DIR}/C03BC-Procurement-Rules.dc.html`, scope);
		// Kind-specific values are the fixture's own (the board samples a
		// method-eligibility rule); this asserts the composition, not the data.
		const FIXTURE_VALUES = ["Method", "Procedure", "Category", "Currency"];
		const wanted = (await landmarks(art, scope)).filter((text) => !FIXTURE_VALUES.includes(text));

		await loginAsAdministrator(page);
		// The board samples a method-eligibility rule, but Check sources applies
		// to the verification targets the model actually has (a reference
		// version or a calendar — a method profile carries its own status, plan
		// D10). The composition under test is the same either way.
		const reference = await currentReservationVersion(page);
		const errors = await openSetupTab(page, `procurement-settings/procurement-rules/${reference}`, '[data-testid="kt-procset-rule-card"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C03B-detail", "C03BC#detail");
		await expectBoardStructure(page, '[data-testid="kt-procset-rule-card"]', art, scope, "C03BC#detail");
		// Read-only: a correction is a new version, never an edit in place.
		expect(await page.locator('[data-testid="kt-procset-rule-card"] input').count()).toBe(0);
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// Retargeted from the retired Planning board to CFG's own C04 "#detail".
	test("C04-schedule — Schedule profile detail with its seven milestones", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#detail";
		await openArtboard(art, `${DESIGN_DIR}/C04-Schedules-Calendars.dc.html`, scope);
		// A schedule profile is not one of the model's verification targets (a
		// reference version or a calendar is — `_VERIFICATION_TARGETS`); it
		// carries its own status through its register command. The source-check
		// actions are asserted on the calendar, where they apply.
		const VERIFICATION_TARGET_ACTIONS = ["Check sources", "View usage and history"];
		// The board's selected-interval editor lives in the schedule editor,
		// because a saved version is read-only (DEPARTURES C04#detail).
		// Its words are dropped as one span, from the heading to the end of its
		// field grid, since some ("From", "To") also head the interval table.
		const all = await landmarks(art, scope);
		const start = all.indexOf("Selected interval — Contract signing");
		const end = all.indexOf("Source reference", start);
		const wanted = [...all.slice(0, start), ...all.slice(end + 1)].filter((text) => !VERIFICATION_TARGET_ACTIONS.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/schedule-profiles/SPR-OPEN-TENDER-GOODS-V1", '[data-testid="kt-procset-profile-table"]');
		expectBoardLandmarks(wanted, await landmarks(page, LIVE_SCOPE), "C04-schedule", "C04#detail");
		await expectBoardStructure(page, '[data-testid="kt-procset-profile-table"]', art, "#detail > div", "C04#detail");
		// Seven milestones, and the six intervals between them.
		expect(await page.locator('[data-testid^="kt-procset-milestone-"]').count()).toBe(7);
		expect(await page.locator('[data-testid^="kt-procset-interval-"]').count()).toBe(6);
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

});
