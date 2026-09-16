import { test, expect, Page } from "@playwright/test";
import { loginAsAdministrator } from "../../helpers/auth";
import {
	openArtboard,
	landmarks,
	expectLandmarkSubsequence,
	widthRatio,
	boxWidth,
	rowHeightByText,
	gridLabelColumn,
	textFits,
	collectPageErrors,
	expectClose,
	openFrame,
} from "../../helpers/designFidelity";

/**
 * System setup design-fidelity gate (AGENTS.md §6.6 enforcement).
 *
 * For every System setup screen with a `.dc.html` artboard, this spec renders
 * the artboard itself and derives the expectations from that render:
 *
 *   - the artboard's ordered structural landmarks must appear in order in the
 *     live page (composition), and
 *   - geometry measured off the artboard (column split, row heights, dialog
 *     widths, grid label columns, truncation state of named fixture text)
 *     must match the live measurement within tolerance.
 *
 * Prerequisite state: the KT-STD §8 seed world
 * (`bench execute kentender_core.seeds.site_setup.run` — idempotent; the
 * `ui-system-setup-fidelity-gate` make target runs it first).
 *
 * Known, deliberate fixture deltas NOT asserted here: record ids and codes
 * (tracker C4, resolved: codes are server-generated OU-{suffix}-{sequence};
 * the artboards' mnemonic chips are historical fixture data), names, dates.
 * Data is the seed's business; this gate owns structure and geometry.
 */

const DESIGN_DIR = "docs/mvp-1-r1/09_unified_system_setup/design";
const PLN_DESIGN = "docs/mvp-1-r1/04_planning/design/C01-C04-Setup.dc.html";
const LIVE_SCOPE = ".kt-setup-shell";
const DIALOG_SCOPE = ".kt-dialog";

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

async function filterRegisterTo(page: Page, text: string): Promise<void> {
	await page.fill('[data-testid="kt-ura-search"]', text);
	await page.waitForSelector(`table.kt-table tbody tr:has-text("${text}")`, { timeout: 15_000 });
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

async function artboardLandmarks(page: Page, file: string, scope: string): Promise<string[]> {
	await openArtboard(page, `${DESIGN_DIR}/${file}`, scope);
	return landmarks(page, scope);
}

test.describe("System setup — design fidelity", () => {
	test("AUTH-DES-01 — Organisation structure tab", async ({ page, browser }) => {
		const artboardScope = '[data-screen-label="AUTH-DES-01"]';
		const art = await browser.newPage();
		await openArtboard(art, `${DESIGN_DIR}/AUTH-DES-01 Organisation structure.dc.html`, artboardScope);
		const wanted = await landmarks(art, artboardScope);
		const artTreeRatio = await widthRatio(art, `${artboardScope} .card`);
		const artRowHeight = await rowHeightByText(art, artboardScope, "Ministry of Health");
		const artPanelCol = await gridLabelColumn(art, `${artboardScope} div[style*="grid-template-columns:130px"]`);
		const artDirectorateFits = await textFits(art, artboardScope, "Directorate of Digital Health and Policy");
		// C4 (tracker, RESOLVED 2026-09-03: codes ARE server-generated
		// OU-{suffix}-{sequence}): the owner-supplied artboards keep their
		// historical mnemonic chips, so live chips are permanently wider.
		// Measure both so the truncation check excuses exactly that data
		// delta and nothing else.
		const artChipWidth = await art.evaluate((scope) => {
			const chip = document.querySelector(`${scope} span[style*="ui-monospace"]`);
			return chip ? chip.getBoundingClientRect().width : 0;
		}, artboardScope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "organisation-structure", '[data-testid="kt-ou-detail"]');
		// Mirror the artboard's selection (the directorate) so the same actions render.
		await page.click('.kt-org-tree-host .tree-link:has-text("Directorate of Digital Health")');
		await page.waitForTimeout(500);

		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "AUTH-DES-01");
		expectClose(await widthRatio(page, ".kt-org-tree-card"), artTreeRatio, 0.02, "tree column ratio");
		expectClose(
			await rowHeightByText(page, ".kt-org-tree-host", "Ministry of Health"),
			artRowHeight,
			2,
			"tree row height"
		);
		expectClose(await gridLabelColumn(page, ".kt-panel-row"), artPanelCol, 1, "panel label column");
		if (artDirectorateFits) {
			// The artboard shows the full directorate name. Live must too, up to
			// the C4 chip-width delta (generated codes are wider than the
			// artboards' historical mnemonic chips — C4 resolved: generated
			// codes are canonical, so this allowance is permanent by design).
			const live = await page.evaluate(() => {
				const label = Array.from(document.querySelectorAll<HTMLElement>(".kt-org-tree-host .tree-label")).find(
					(a) => (a.textContent || "").trim() === "Directorate of Digital Health and Policy"
				);
				const chip = label?.closest(".tree-link")?.querySelector(".kt-tree-code");
				return {
					deficit: label ? label.scrollWidth - label.clientWidth : NaN,
					chipWidth: chip ? chip.getBoundingClientRect().width : 0,
				};
			});
			const allowance = Math.max(0, live.chipWidth - artChipWidth) + 1;
			expect(
				live.deficit,
				`directorate name truncated ${live.deficit}px beyond the C4 chip allowance (${allowance.toFixed(1)}px)`
			).toBeLessThanOrEqual(allowance);
		}
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("AUTH-DES-02 — Add organisation unit dialog", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "AUTH-DES-02 Add organisation unit dialog.dc.html", ".dialog-backdrop .dialog");
		const artWidth = await boxWidth(art, ".dialog-backdrop .dialog");

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "organisation-structure", '[data-testid="kt-ou-detail"]');
		await page.click('[data-testid="kt-ou-add"]');
		await page.waitForSelector('[data-testid="kt-ou-prompt"]');

		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "AUTH-DES-02");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("AUTH-DES-03 — Users and responsibilities register", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(
			art,
			"AUTH-DES-03 Users and responsibilities register.dc.html",
			'[data-screen-label="AUTH-DES-03"]'
		);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "AUTH-DES-03");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("AUTH-DES-04 — Assign responsibility dialog (OU scope with summary)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(
			art,
			"AUTH-DES-04 Assign responsibility - Organisation Unit scope.dc.html",
			".dialog-backdrop .dialog"
		);
		const artWidth = await boxWidth(art, ".dialog-backdrop .dialog");

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');
		await page.click('[data-testid="kt-ura-assign-open"]');
		await page.waitForSelector('[data-testid="kt-ura-assign"]');
		// Reach the artboard's state: user picked, OU-scoped role, unit chosen,
		// server summary rendered. Nothing is submitted.
		await page.fill('[data-testid="kt-ura-user"]', "grace");
		await page.click('.kt-matches button:has-text("Grace Wanjiku")');
		await page.click('[data-testid="kt-ura-role"]');
		await page.click('[data-testid="kt-ura-role-option-Departmental Author"]');
		await page.click('[data-testid="kt-ura-ou-toggle"]');
		await page.click('.kt-matches button:has-text("Digital Health")');
		await page.waitForSelector('[data-testid="kt-ura-summary"]', { timeout: 10_000 });

		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "AUTH-DES-04");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("AUTH-DES-06 — Responsibility detail", async ({ page, browser }) => {
		const artboardScope = '[data-screen-label="AUTH-DES-06"]';
		const art = await browser.newPage();
		await openArtboard(art, `${DESIGN_DIR}/AUTH-DES-06 Responsibility detail.dc.html`, artboardScope);
		const wanted = await landmarks(art, artboardScope);
		const artLabelCol = await gridLabelColumn(art, `${artboardScope} div[style*="grid-template-columns:200px"]`);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');
		// Any Active assignment renders the artboard's full composition. The
		// register lists newest rows first and this site's register churns
		// (seed reconciliations, test worlds), so filter to Grace rather than
		// assuming her rows sit on the first page.
		await filterRegisterTo(page, "Grace Wanjiku");
		await page.click('table.kt-table tbody tr:has-text("Grace Wanjiku") a');
		await page.waitForSelector('[data-testid="kt-ura-history"]', { timeout: 15_000 });

		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "AUTH-DES-06");
		expectClose(await gridLabelColumn(page, ".kt-detail-row"), artLabelCol, 1, "detail label column");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("AUTH-DES-07 — Revoke responsibility dialog", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(
			art,
			"AUTH-DES-07 Revoke responsibility dialog.dc.html",
			".dialog-backdrop .dialog"
		);
		const artWidth = await boxWidth(art, ".dialog-backdrop .dialog");

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "users-and-responsibilities", '[data-testid="kt-ura-table"]');
		await filterRegisterTo(page, "Grace Wanjiku");
		await page.click('table.kt-table tbody tr:has-text("Grace Wanjiku") a');
		await page.waitForSelector('[data-testid="kt-ura-open-revoke"]', { timeout: 15_000 });
		await page.click('[data-testid="kt-ura-open-revoke"]');
		await page.waitForSelector('[data-testid="kt-ura-revoke"]');

		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "AUTH-DES-07");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

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
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C01-configured");
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
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C01-conflict");
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
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C02-overview");
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
		const errors = await openSetupTab(page, "fiscal-years/year/2027-2028", '[data-testid="kt-setup-fy-detail-card"]');
		// The artboard draws the history table expanded; the live disclosure
		// starts collapsed, so open it before comparing landmarks.
		await page.click('[data-testid="kt-fy-history-toggle"]');
		await page.waitForSelector('[data-testid="kt-fy-history-body"] table');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C02-detail");
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
		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "C02-add-year");

		// The exact duplicate defect, and Add disabled with it (CFG-UX-AC-05).
		// The Company defect shares that treatment and is proven server-side in
		// kentender_core.tests.test_site_configuration.
		await page.fill('[data-testid="kt-fy-start-year"]', "2027");
		await page.waitForSelector('[data-testid="kt-fy-duplicate"]');
		await expect(page.locator('[data-testid="kt-fy-duplicate"]')).toHaveText(
			"Duplicate. This financial year already exists."
		);
		await expect(page.locator('[data-testid="kt-fy-add-confirm"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-open-form — Open submissions form with the cross-year replacement notice", async ({ page, browser }) => {
		const art = await browser.newPage();
		// First card in the forms grid: Open · Departmental needs.
		const scope = "#forms .card";
		await openArtboard(art, `${DESIGN_DIR}/C02-Financial-Years.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years/year/2026-2027", '[data-testid="kt-setup-fy-detail-card"]');
		// §8.4 world: 2027/28 holds needs intake, so opening it for 2026/27
		// shows the replacement notice. Nothing is submitted.
		await page.click('[data-testid="kt-fy-open-needs"]');
		await page.waitForSelector('[data-testid="kt-fy-intake-replaces"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "C02-open-form");
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
		const errors = await openSetupTab(page, "fiscal-years/year/2027-2028", '[data-testid="kt-setup-fy-detail-card"]');
		await page.click('[data-testid="kt-fy-deadline-needs"]');
		await page.waitForSelector('[data-testid="kt-fy-intake"][data-mode="deadline"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "C02-deadline-form");
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
		const errors = await openSetupTab(page, "fiscal-years/year/2027-2028", '[data-testid="kt-setup-fy-detail-card"]');
		await page.click('[data-testid="kt-fy-disable-open"]');
		await page.waitForSelector('[data-testid="kt-fy-disable"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "C02-disable");
		await expect(page.locator('[data-testid="kt-fy-disable-blocker"]').first()).toHaveText(
			"Departmental needs submission is open for this financial year."
		);
		await expect(page.locator('[data-testid="kt-fy-disable-confirm"]')).toBeDisabled();
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// CFG-CHG-002 v0.11 §10.5 — C03A-Funding-Sources.dc.html (Phase 3C). The
	// board carries no anchor ids, so `document.querySelector` takes the
	// first `.blueprint` (the list) and the first `.dialog` (the editor).
	test("C03A-list — Funding sources list with the availability column", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = ".blueprint";
		await openArtboard(art, `${DESIGN_DIR}/C03A-Funding-Sources.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings", '[data-testid="kt-procset-sources"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03A-list");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03A-editor — the availability choice states what it governs, and a duplicate name is refused before submit", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = ".dialog";
		await openArtboard(art, `${DESIGN_DIR}/C03A-Funding-Sources.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/new-source", '[data-testid="kt-procset-source-editor"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03A-editor");

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
		const errors = await openSetupTab(page, "procurement-settings/new-rule", '[data-testid="kt-procset-rule-editor"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03B-add");
		expect(await page.locator('[data-testid="kt-rule-kind"] option').allTextContents()).toEqual([
			"Method eligibility",
			"Reservation rules",
			"Exclusive preference",
			"Preference margins",
			"Market price index",
			"Approval applicability",
			"Publication obligations",
		]);
		// Method eligibility is owned by its method profile (plan D10), so the
		// editor says so rather than offering a divergent second form.
		await page.selectOption('[data-testid="kt-rule-kind"]', "Method eligibility");
		await expect(page.locator('[data-testid="kt-rule-delegated"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-rule-save"]')).toBeDisabled();
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
			`procurement-settings/check-sources/${reference}`,
			'[data-testid="kt-source-check-rule"]'
		);
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03D-pending");

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
		// The board's second `.blueprint` in this section is the calendar
		// editor; `#calendar` scopes to the whole missing/add/detail group.
		const scope = "#calendar .blueprint";
		await openArtboard(art, `${DESIGN_DIR}/C04-Schedules-Calendars.dc.html`, scope);
		// This one board documents both states at once: the unsaved editor
		// (Cancel / Save calendar version, Add row) and the saved detail
		// (Create new version / Check sources / View usage and history). A
		// live screen is only ever in one of them, so each set of actions is
		// asserted in the state it belongs to rather than both at once.
		const SAVED_ONLY = ["Create new version", "Check sources", "View usage and history"];
		const wanted = (await landmarks(art, scope)).filter((text) => !SAVED_ONLY.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/new-calendar", '[data-testid="kt-procset-calendar"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C04-calendar");
		await expect(page.locator('[data-testid="kt-cal-weekend-Saturday"]')).toBeChecked();
		await expect(page.locator('[data-testid="kt-cal-weekend-Sunday"]')).toBeChecked();
		await expect(page.locator('[data-testid="kt-cal-add-holiday"]')).toBeVisible();

		// The saved state: read-only, no row controls, and the successor action.
		const calendar = await firstCalendar(page);
		if (calendar) {
			await page.goto(`/app/system-setup#procurement-settings/calendar/${calendar}`, { waitUntil: "domcontentloaded" });
			await page.waitForSelector('[data-testid="kt-cal-name-ro"]', { timeout: 20_000 });
			await expect(page.locator('[data-testid="kt-cal-new-version"]')).toBeVisible();
			await expect(page.locator('[data-testid="kt-cal-add-holiday"]')).toHaveCount(0);
		}
		// Nothing is saved: a calendar version is immutable once written.
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	// CFG-CHG-002 v0.11 §10.10 — Reminders.dc.html (Phase 3G). The board's
	// first `.blueprint` is the unchanged specimen; the card states what is
	// being set, its unit and both consequences.
	test("Reminders — the threshold states what it sets, its unit and that it is not a deadline", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = ".blueprint";
		await openArtboard(art, `${DESIGN_DIR}/Reminders.dc.html`, scope);
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings", '[data-testid="kt-procset-reminder"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "Reminders");
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

	// Retargeted from the retired Planning board to CFG's own C03BC "#detail"
	// (Phase 3D). The saved detail states its groups and its actions; nothing
	// on it is editable, because a correction is a new version (§11.6).
	test("C03B-detail — a saved rule Version, read-only", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = "#detail";
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
		const errors = await openSetupTab(page, `procurement-settings/rule/${reference}`, '[data-testid="kt-procset-rule-card"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03B-detail");
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
		const wanted = (await landmarks(art, scope)).filter((text) => !VERIFICATION_TARGET_ACTIONS.includes(text));

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/profile/SPR-OPEN-TENDER-GOODS-V1", '[data-testid="kt-procset-profile-table"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C04-schedule");
		// Seven milestones, and the six intervals between them.
		expect(await page.locator('[data-testid^="kt-procset-milestone-"]').count()).toBe(7);
		expect(await page.locator('[data-testid^="kt-procset-interval-"]').count()).toBe(6);
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

});
