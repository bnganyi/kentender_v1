/**
 * P9-09 — Overview tab: next step, summary, lineage, key dates (doc 9 §17.2).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Overview tab (P9-09)', () => {
	test.setTimeout(180_000);

	test('Overview tab shows structured sections when a tender is selected', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await expect(shell.getByTestId('tm2-tab-panel-overview')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await expect(shell.getByTestId('tm2-tab-panel-overview')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });
		await expect(shell.getByTestId('tm2-overview-next-step')).toBeVisible();
		await expect(shell.getByTestId('tm2-overview-package-lineage')).toBeVisible();
		await expect(shell.getByTestId('tm2-overview-key-dates')).toBeVisible();
		await expect(shell.getByTestId('tm2-overview-recent-events')).toBeVisible();

		await shell.getByTestId('tm2-tab-overview').click();
		await expect(shell.getByTestId('tm2-overview-tab-counts')).toBeVisible();
	});
});
