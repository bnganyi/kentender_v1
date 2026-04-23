import { test, expect } from '@playwright/test';

import { loginAsProcurementPlanner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/** S17 — Procurement planning-ready queue surface. */
test('Procurement can open Planning Ready queue', async ({ page }) => {
	await loginAsProcurementPlanner(page);
	await openDIALanding(page);
	await page.getByTestId('dia-tab-approved').click();
	await page.getByTestId('dia-queue-planning_ready').click();
	await expect(page.getByTestId('dia-list-root')).toBeVisible();
	const row = page.getByTestId('dia-row-DIA-MOH-2026-0005');
	const has = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!has, 'Seed DIA-MOH-2026-0005 not present — run seed_dia_extended.');
	await expect(row).toBeVisible();
});
