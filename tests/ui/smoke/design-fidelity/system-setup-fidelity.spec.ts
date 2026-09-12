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

	// PLN-CHG-001 v1.18 §10.11 — the C01–C04 frames supersede CFG-DES-01/03
	// as the fidelity source for the Procuring entity, Fiscal years and
	// Procurement settings tabs (plan D13); CFG-DES-04/05 stay for the
	// add-year and needs-intake dialogs.
	test("C01-configured — Procuring entity tab with route and county flag", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C01-configured");
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
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C01-conflict — county applicability mismatch shown inline, nothing saved", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C01-conflict");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procuring-entity", '[data-testid="kt-setup-pe-record"]');
		const typeBefore = await page.locator('[data-testid="kt-setup-pe-type"]').inputValue();
		await page.selectOption('[data-testid="kt-setup-pe-type"]', "County Government");
		if (await page.locator('[data-testid="kt-setup-pe-county"]').isChecked()) {
			await page.uncheck('[data-testid="kt-setup-pe-county"]');
		}
		await page.click('[data-testid="kt-setup-pe-submit"]');
		await page.waitForSelector('[data-testid="kt-setup-pe-county-conflict"]');
		expect(await page.locator('[data-testid="kt-setup-pe-county-conflict"]').textContent()).toContain(
			"County applicability does not match the entity details. Review the configuration."
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
			errors.filter((e) => !e.includes("County applicability does not match") && !/status of 417/.test(e)),
			"console errors"
		).toEqual([]);
		await art.close();
	});

	test("C02 — Fiscal years tab with the departmental-plan intake dialog", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C02");
		const wanted = await landmarks(art, scope);
		const artDialogWidth = await boxWidth(art, `${scope} .dialog`);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years", '[data-testid="kt-fy-table"]');
		// §8.4 world: 2027/28 is open for departmental-plan intake, 2026/27 is
		// closed — managing the closed year opens the "Open" dialog, the
		// artboard's state. Nothing is submitted.
		await page.click('[data-testid="kt-fy-open-plan-2026-2027"]');
		await page.waitForSelector('[data-testid="kt-fy-intake"][data-purpose="plan"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C02");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artDialogWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C02-close — Close departmental-plan intake dialog", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C02-close");
		const wanted = await landmarks(art, `${scope} .dialog`);
		const artDialogWidth = await boxWidth(art, `${scope} .dialog`);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years", '[data-testid="kt-fy-table"]');
		await page.click('[data-testid="kt-fy-close-plan-2027-2028"]');
		await page.waitForSelector('[data-testid="kt-fy-intake"][data-purpose="plan"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "C02-close");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artDialogWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03 — Procurement settings: funding sources and procurement rules", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C03");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings", '[data-testid="kt-procset-rules"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03-source-editor — Edit funding source", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C03-source-editor");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings", '[data-testid="kt-procset-sources"]');
		await page.click('[data-testid="kt-procset-source-edit-Government of Kenya"]');
		await page.waitForSelector('[data-testid="kt-procset-source-editor"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03-source-editor");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C03-detail — a referenced rule Version, read-only", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C03-detail");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/rule/MPR-OPEN-TENDER-V1", '[data-testid="kt-procset-rule-card"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C03-detail");
		expect(await page.locator('[data-testid="kt-procset-rule-card"] input').count()).toBe(0);
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C04 — Schedule profile", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C04");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings/profile/SPR-OPEN-TENDER-GOODS-V1", '[data-testid="kt-procset-profile-table"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C04");
		expect(await page.locator('[data-testid="kt-procset-profile-table"] tbody tr').count()).toBe(7);
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("C04-eligibility-reminder — reminder threshold card", async ({ page, browser }) => {
		const art = await browser.newPage();
		const scope = await openFrame(art, PLN_DESIGN, "C04-eligibility-reminder");
		const wanted = await landmarks(art, scope);

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "procurement-settings", '[data-testid="kt-procset-reminder"]');
		expectLandmarkSubsequence(wanted, await landmarks(page, LIVE_SCOPE), "C04-eligibility-reminder");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("CFG-DES-04 — Add financial year dialog", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(art, "CFG-DES-04 Add financial year dialog.dc.html", ".dialog-backdrop .dialog");
		const artWidth = await boxWidth(art, ".dialog-backdrop .dialog");

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years", '[data-testid="kt-fy-table"]');
		await page.click('[data-testid="kt-fy-add-open"]');
		await page.waitForSelector('[data-testid="kt-fy-add"]');
		// Reach the artboard's state: a start year entered, server preview shown.
		await page.fill('[data-testid="kt-fy-start-year"]', "2028");
		await page.waitForSelector('[data-testid="kt-fy-preview"]', { timeout: 10_000 });

		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "CFG-DES-04");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});

	test("CFG-DES-05 — Open needs submission dialog (with replacement notice)", async ({ page, browser }) => {
		const art = await browser.newPage();
		const wanted = await artboardLandmarks(
			art,
			"CFG-DES-05 Open needs submission dialog.dc.html",
			".dialog-backdrop .dialog"
		);
		const artWidth = await boxWidth(art, ".dialog-backdrop .dialog");

		await loginAsAdministrator(page);
		const errors = await openSetupTab(page, "fiscal-years", '[data-testid="kt-fy-table"]');
		// §8.4 world: 2027/28 is open, so opening 2026/27 shows the replacement
		// notice — the artboard's exact state. Nothing is submitted.
		await page.click('[data-testid="kt-fy-open-2026-2027"]');
		await page.waitForSelector('[data-testid="kt-fy-intake-replaces"]');

		expectLandmarkSubsequence(wanted, await landmarks(page, DIALOG_SCOPE), "CFG-DES-05");
		expectClose(await boxWidth(page, DIALOG_SCOPE), artWidth, 2, "dialog width");
		expect(errors, "console errors").toEqual([]);
		await art.close();
	});
});
