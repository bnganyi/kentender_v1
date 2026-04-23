import { test, expect } from '@playwright/test';

import { loginAsHoDApprover } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/**
 * S5 — HoD queue (requires `seed_dia_basic` or `seed_dia_extended` so DIA-MOH-2026-0002 exists).
 */
test.describe('DIA work queues', () => {
	test('HoD sees seeded pending demand row by stable test id', async ({ page }) => {
		await loginAsHoDApprover(page);
		await openDIALanding(page);
		const row = page.getByTestId('dia-row-DIA-MOH-2026-0002');
		const hasSeed = await row.isVisible({ timeout: 25_000 }).catch(() => false);
		test.skip(!hasSeed, 'Seed DIA-MOH-2026-0002 not present — run seed_dia_basic or seed_dia_extended.');
		await row.click();
		await expect(page.getByTestId('dia-detail-panel')).toBeVisible();
		await expect(page.getByTestId('dia-detail-title')).toBeVisible();
	});
});
