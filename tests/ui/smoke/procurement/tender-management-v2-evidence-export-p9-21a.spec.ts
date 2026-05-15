/**
 * P9-21a — Evidence export: header control + export panel (doc 9 §14.5, §13.3).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench evidence export (P9-21a)', () => {
	test.setTimeout(180_000);

	test('header Evidence Export opens §13.3 export panel when a tender is selected', async ({ page, baseURL }) => {
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
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-overview-tender-summary')).toBeVisible({ timeout: 60_000 });

		const hdrBtn = shell.getByTestId('tm2-action-evidence-export');
		await expect(hdrBtn).toBeVisible();
		const disabled = await hdrBtn.isDisabled().catch(() => true);
		if (disabled) {
			return;
		}

		await hdrBtn.click();
		const panel = page.getByTestId('tm2-evidence-export-panel');
		await expect(panel).toBeVisible({ timeout: 30_000 });
		await expect(panel.getByTestId('tm2-evidence-export-status')).toBeVisible();
	});
});
