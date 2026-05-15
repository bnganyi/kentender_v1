/**
 * P9-12 — Supplier Access tab: access rule + invitations + participation (doc 9 §17.5).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Supplier Access tab (P9-12)', () => {
	test.setTimeout(180_000);

	test('Supplier Access tab shows access rule and participation sections when a tender is selected', async ({
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

		const tab = shell.getByTestId('tm2-tab-supplier-access');
		await expect(tab).toBeVisible();
		await expect(tab).toBeEnabled();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-supplier-access')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-supplier-access')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });

		await tab.click();
		await expect(shell.getByTestId('tm2-sa-access-rule')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-sa-invitations')).toBeVisible();
		await expect(shell.getByTestId('tm2-sa-participation')).toBeVisible();
		await expect(shell.getByTestId('tm2-sa-readonly-notice')).toBeVisible();
	});
});
