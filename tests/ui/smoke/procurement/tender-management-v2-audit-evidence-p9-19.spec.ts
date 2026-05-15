/**
 * P9-19 — Audit & Evidence tab: lifecycle + export entry (doc 9 §17.12, doc 6 §25).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Audit & Evidence tab (P9-19)', () => {
	test.setTimeout(180_000);

	test('Audit & Evidence tab shows lifecycle area and export control', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const tab = shell.getByTestId('tm2-tab-audit-evidence');
		await expect(tab).toBeVisible();
		await expect(tab).toBeEnabled();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-audit-evidence')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-audit-evidence')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });

		await tab.click();
		await expect(shell.getByTestId('tm2-ae-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-ae-export-notice')).toBeVisible();
		await expect(shell.getByTestId('tm2-ae-lifecycle-wrap')).toBeVisible();
		await expect(shell.getByTestId('tm2-ae-sensitive-wrap')).toBeVisible();
		await expect(shell.getByTestId('tm2-ae-action-export')).toBeVisible();
	});
});
