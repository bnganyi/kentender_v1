import { test, expect, type Page } from "@playwright/test";

import { loginAsAdministrator } from "../../helpers/auth";
import { installOfflineAssetGuard, openNativeDashboard } from "../../helpers/itWizardDesk";

/**
 * PW-ITW-DASH-VIS-01 — Screen 01 visual-fidelity snapshot gate.
 *
 * Locks the "exactly as designed" chrome + layout + brand typography of the
 * native IT Tender Configurations dashboard (mockup: IT-STD-Wizard-v2 screen-01
 * code.html). Data-driven regions (KPI values/bars, table rows, pager counts,
 * filter chips, the avatar initials) are masked so the baseline is stable across
 * seed churn — the snapshot asserts the fixed top app bar, page header, search/
 * filter toolbar, table frame, footer toolbar, and the self-hosted fonts render.
 *
 * Baseline lives in dashboard-visual.spec.ts-snapshots/. Regenerate intentionally
 * with `npx playwright test dashboard-visual.spec.ts --update-snapshots` after a
 * deliberate design change. Run via `make it-wizard-screen-01-gate`.
 */
test.describe.serial("IT Wizard dashboard visual fidelity", () => {
	let page: Page;

	test.beforeAll(async ({ browser }) => {
		page = await browser.newPage();
		await page.setViewportSize({ width: 1440, height: 900 });
		await installOfflineAssetGuard(page);
		await loginAsAdministrator(page);
	});

	test.afterAll(async () => {
		await page.close();
	});

	test("matches the approved design chrome", async () => {
		await openNativeDashboard(page);
		// Ensure self-hosted fonts are resolved before snapshotting.
		await page.evaluate(() => (document as unknown as { fonts: FontFaceSet }).fonts.ready);
		await expect(page.locator('[data-testid="it-wizard-dashboard"]')).toBeVisible();

		await expect(page).toHaveScreenshot("dashboard-screen-01.png", {
			fullPage: true,
			animations: "disabled",
			// Mask everything data-driven so the gate tracks design, not seed data.
			mask: [
				page.locator("[data-itw-kpi-grid]"),
				page.locator("[data-itw-tbody]"),
				page.locator("[data-itw-table-footer]"),
				page.locator("[data-itw-filter-chips]"),
				page.locator(".kt-itw-avatar"),
			],
			maxDiffPixelRatio: 0.02,
		});
	});
});
