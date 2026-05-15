/**
 * P9-03 — New Tender opens package picker modal (doc 9 §14.5); must not open TM2 Tender new form.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management New Tender package picker (P9-03)', () => {
	test.setTimeout(180_000);

	test('New Tender opens tm2-new-tender-wizard with package picker; URL stays on workbench', async ({
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
		await expect(wiz.getByTestId('tm2-package-picker')).toBeVisible();
		await expect(wiz.getByTestId('tm2-package-picker-search')).toBeVisible();
		await expect(wiz.getByTestId('tm2-package-picker-table')).toBeVisible({ timeout: 60_000 });

		await expect(page).toHaveURL(/tender-management-v2/i);
		await expect(page).not.toHaveURL(/TM2%20Tender.*\/new|tm2-tender.*\/new/i);

		await page.getByRole('button', { name: 'Cancel', exact: true }).click();
		await expect(wiz).toBeHidden({ timeout: 15_000 });
	});
});
