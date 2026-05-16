/**
 * R4-006 / LV-R4-006-01 — Journey header (`plc-journey-header`, title, entity, category, method, stage, next action).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksMasterJourneyHeader,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('Procurement Journey header (R4-006)', () => {
	test('PLC-R4-006-01: path URL loads header bound to get_journey (WORKS seed)', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
	});

	test('PLC-R4-006-02: base journey URL shows empty hint (no API call required)', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/desk/plc-procurement-journey', { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('plc-journey-page')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('plc-journey-empty-hint')).toBeVisible();
		await expect(page.getByTestId('plc-journey-header')).toHaveCount(0);
	});
});
