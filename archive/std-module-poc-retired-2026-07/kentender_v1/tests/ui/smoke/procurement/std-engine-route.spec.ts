/**
 * STD-LIB-0001 / STD-CFG-0610 — std-engine redirects to v2 std-library; std-engine-advanced → legacy shell.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('STD Engine route (STD-LIB-0001 / 0100)', () => {
	test.setTimeout(180_000);

	test('std-engine redirects to v2 STD Library (not legacy shell)', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page).toHaveURL(/std-library/i, { timeout: 90_000 });
	});

	test('desk/std-engine redirects to v2 STD Library', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/desk/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page).toHaveURL(/std-library/i, { timeout: 90_000 });
	});

	test('std-engine/library/import redirects to v2 import wizard', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library/import`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-import-root"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-lib-import-steps"]')).toBeVisible();
		await expect(page).toHaveURL(/std-library\/import/i, { timeout: 90_000 });
	});

	test('std-engine-advanced opens legacy library shell', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine-advanced`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-header-title"]')).toHaveText(
			'Official STD Library',
		);
		await expect(shell.locator('[data-testid="std-library-list"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-detail-panel"]')).toBeVisible();
	});
});
