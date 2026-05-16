/**
 * R4-005 / LV-R4-005-01 / G0-007 — Procurement Journey Desk route with `<journey_code>` path segment
 * (`/desk/plc-procurement-journey/<journey_code>`), shell selector `plc-journey-page`.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksMasterJourneyHeader,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';
const JOURNEY_PATH_RE = /\/(app|desk)\/plc-procurement-journey\/JRN-MOH-2026-001/;

test.describe('Procurement Journey route (R4-005)', () => {
	test('PLC-R4-005-01: direct /desk/.../<journey_code> loads plc-journey-page', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expect(page).toHaveURL(JOURNEY_PATH_RE, { timeout: 45_000 });
	});

	test('PLC-R4-005-02: query ?journey_code= still resolves (compat)', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/desk/plc-procurement-journey?journey_code=${encodeURIComponent(WORKS_JOURNEY_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
	});

	test('PLC-R4-005-03: Open Journey from Procurement Home uses path segment', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expect(page.getByTestId('ph-landing-page')).toBeVisible({ timeout: 45_000 });

		const card = page
			.locator('.plc-procurement-home-active-journeys')
			.locator('.kt-ph-journey-card')
			.filter({ hasText: /District Hospital Renovation Works/i });
		await expect(card).toBeVisible({ timeout: 45_000 });
		await card.locator('.plc-home-open-journey').first().click();

		await expect(page).toHaveURL(JOURNEY_PATH_RE, { timeout: 45_000 });
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
	});
});
