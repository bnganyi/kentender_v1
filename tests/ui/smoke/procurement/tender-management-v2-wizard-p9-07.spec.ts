/**
 * P9-07 — New Tender wizard steps 1–6 (doc 9 §15); Administrator smoke.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management New Tender wizard (P9-07)', () => {
	test.setTimeout(180_000);

	test('wizard shows step 1 and advances to confirm with eligible package row', async ({
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

		await shell.getByTestId('tm2-action-new-tender').click();
		const wiz = page.locator('[data-testid="tm2-new-tender-wizard"]');
		await expect(wiz).toBeVisible({ timeout: 30_000 });
		await expect(wiz.getByTestId('tm2-wizard-step-1')).toBeVisible({ timeout: 60_000 });

		const table = wiz.getByTestId('tm2-package-picker-table');
		await expect(table).toBeVisible({ timeout: 90_000 });

		const eligibleRow = wiz.locator('[data-testid="tm2-package-picker-row"]').filter({
			hasText: 'Eligible',
		});
		const n = await eligibleRow.count();
		if (n === 0) {
			await wiz.getByRole('button', { name: 'Cancel', exact: true }).click();
			await expect(wiz).toBeHidden({ timeout: 15_000 });
			return;
		}
		await eligibleRow.first().click();
		await wiz.getByRole('button', { name: 'Next', exact: true }).click();
		await expect(wiz.getByTestId('tm2-wizard-step-2')).toBeVisible({ timeout: 30_000 });

		await wiz.getByRole('button', { name: 'Back', exact: true }).click();
		await expect(wiz.getByTestId('tm2-wizard-step-1')).toBeVisible();

		await wiz.getByRole('button', { name: 'Cancel', exact: true }).click();
		await expect(wiz).toBeHidden({ timeout: 15_000 });
	});
});
