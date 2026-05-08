/**
 * STD-LIB-0001 / STD-LIB-0100 — std-engine library shell; std-engine-advanced → STD Template list.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('STD Engine route (STD-LIB-0001 / 0100)', () => {
	test.setTimeout(180_000);

	test('std-engine opens Official STD Library shell (not workspace redirect)', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="std-library-header-title"]')).toHaveText(
			'Official STD Library',
		);
		await expect(page).toHaveURL(/library/i, { timeout: 90_000 });
	});

	test('desk/std-engine shows library shell in page body', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/desk/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({
			timeout: 90_000,
		});
	});

	test('std-engine/library/import opens import wizard shell', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library/import`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-package-import-page"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="std-package-import-stepper"]')).toBeVisible();
		await expect(page).toHaveURL(/std-engine\/library\/import/i, { timeout: 90_000 });
	});

	test('std-engine-advanced opens STD Template list', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine-advanced`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('body')).toContainText(/STD\s+Template/i, { timeout: 90_000 });
		await expect(
			page.locator('.frappe-list, .list-row-head, .standard-list-section').first(),
		).toBeVisible({ timeout: 60_000 });
	});
});
