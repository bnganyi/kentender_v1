/**
 * STD-CFG import wizard smoke.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('STD Config UI — Import wizard', () => {
	test.setTimeout(180_000);

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('import route renders six-step wizard shell', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library/import`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-import-root"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-lib-import-steps"]')).toBeVisible();
	});
});
