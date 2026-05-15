/**
 * P9-16 — Opening Readiness tab: DOM ref + Works arithmetic notice (doc 9 §17.9, smoke TM2-SMOKE-UI-007).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Opening Readiness tab (P9-16)', () => {
	test.setTimeout(180_000);

	test('Opening Readiness tab shows DOM row and optional arithmetic notice', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const tab = shell.getByTestId('tm2-tab-opening-readiness');
		await expect(tab).toBeVisible();
		await expect(tab).toBeEnabled();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-opening-readiness')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await tab.click();
			await expect(shell.getByTestId('tm2-tab-panel-opening-readiness')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });

		await tab.click();
		await expect(shell.getByTestId('tm2-or-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-or-dom-ref')).toBeVisible();
		const warn = shell.getByTestId('tm2-or-arithmetic-warning');
		if (await warn.isVisible().catch(() => false)) {
			await expect(warn).toContainText(/Arithmetic correction/i);
		}
		await expect(shell.getByTestId('tm2-or-opening-rules')).toBeVisible();
	});
});
