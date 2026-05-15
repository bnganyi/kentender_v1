/**
 * P9-06 — Tender list rows: business code, status, blockers (doc 9 §14.8).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management tender list (P9-06)', () => {
	test.setTimeout(180_000);

	test('list rows container loads; row or empty state; deadline + blockers testids', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const rows = shell.getByTestId('tm2-tender-list-rows');
		await expect(rows).toBeVisible({ timeout: 60_000 });
		await expect(rows.locator('[data-testid="tm2-tender-list-row"], [data-testid="tm2-tender-list-empty"]').first()).toBeVisible({
			timeout: 60_000,
		});

		const row = rows.getByTestId('tm2-tender-list-row').first();
		if (await row.isVisible().catch(() => false)) {
			await expect(row).toContainText(/TND-|tender/i);
			await expect(row.getByTestId('tm2-tender-list-row-deadline')).toBeVisible();
			await expect(row.getByTestId('tm2-tender-list-row-blockers')).toBeVisible();
		}
	});
});
