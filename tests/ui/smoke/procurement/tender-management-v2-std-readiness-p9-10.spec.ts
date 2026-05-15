/**
 * P9-10 — STD & Readiness tab: binding, checklist, read-only derived outputs (doc 9 §17.3, TM2-SMOKE-UI-003).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench STD & Readiness tab (P9-10)', () => {
	test.setTimeout(180_000);

	test('STD & Readiness tab shows binding and derived output rows when a tender is selected', async ({
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

		const stdTab = shell.getByTestId('tm2-tab-std-readiness');
		await expect(stdTab).toBeVisible();
		await expect(stdTab).toBeEnabled();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await stdTab.click();
			await expect(shell.getByTestId('tm2-tab-panel-std-readiness')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await stdTab.click();
			await expect(shell.getByTestId('tm2-tab-panel-std-readiness')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });

		await stdTab.click();
		await expect(shell.getByTestId('tm2-std-binding-block')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-std-readiness-checklist')).toBeVisible();
		await expect(shell.getByTestId('tm2-std-derived-outputs')).toBeVisible();
		await expect(shell.getByTestId('tm2-std-derived-bundle')).toBeVisible();
		await expect(shell.getByTestId('tm2-std-derived-dsm')).toBeVisible();
	});
});
