/**
 * P9-13 — Clarifications tab: read-only notice, status chips, thread table (doc 9 §17.6).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Clarifications tab (P9-13)', () => {
	test.setTimeout(180_000);

	test('Clarifications tab shows notice, chips, and table when a tender is selected', async ({
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

		const tab = shell.getByTestId('tm2-tab-clarifications');
		await expect(tab).toBeVisible();
		await expect(tab).toBeEnabled();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-clarifications')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-clarifications')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });

		await tab.click();
		await expect(shell.getByTestId('tm2-clar-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-clar-status-chips')).toBeVisible();
		await expect(shell.getByTestId('tm2-clar-rows')).toBeVisible();
	});
});
