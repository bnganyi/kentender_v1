/**
 * R5-001 / LV-R5-001-01 — Shared module journey context header (`plc-module-journey-context-header`).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('Module journey context header (R5-001)', () => {
	test('PLC-R5-001-01: TM2 tender resolves WORKS journey on smoke page', async ({ page }) => {
		await loginAsAdministrator(page);
		const qs = new URLSearchParams({
			object_type: 'TM2 Tender',
			object_code: WORKS_TENDER_CODE,
		});
		await page.goto(`/desk/plc-module-journey-context?${qs.toString()}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('plc-module-journey-context-page')).toBeVisible({
			timeout: 45_000,
		});
		const header = page.getByTestId('plc-module-journey-context-header');
		await expect(header).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('plc-module-journey-context-title')).toContainText(
			/District Hospital Renovation Works/i,
			{ timeout: 45_000 },
		);
		await expect(page.getByTestId('plc-module-journey-context-code')).toContainText(WORKS_JOURNEY_CODE);
		await expect(page.getByTestId('plc-module-journey-context-open')).toBeVisible();
	});

	test('PLC-R5-001-02: unknown object shows empty state', async ({ page }) => {
		await loginAsAdministrator(page);
		const qs = new URLSearchParams({
			object_type: 'TM2 Tender',
			object_code: 'NO-SUCH-TENDER-999',
		});
		await page.goto(`/desk/plc-module-journey-context?${qs.toString()}`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('plc-module-journey-context-empty')).toBeVisible({
			timeout: 45_000,
		});
	});

	test('PLC-R5-001-03: missing query shows helper copy', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto('/desk/plc-module-journey-context', { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('plc-module-journey-context-missing-params')).toBeVisible({
			timeout: 45_000,
		});
	});
});
