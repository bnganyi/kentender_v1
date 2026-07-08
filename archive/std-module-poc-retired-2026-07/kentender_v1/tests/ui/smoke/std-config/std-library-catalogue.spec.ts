/**
 * STD-CFG-0100 / 0700 — STD Library v2 catalogue page smoke (1.lib mockup fidelity).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('STD Config UI — Library catalogue (STD-CFG-0100)', () => {
	test.setTimeout(180_000);

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('std-library page loads catalogue shell matching 1.lib regions', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-lib-topbar"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-topbar"]')).toHaveCSS('position', 'sticky');
		await expect(page.locator('[data-testid="kt-std-lib-topbar-title"]')).toHaveText(/STD Library/i);
		await expect(page.locator('[data-testid="kt-std-lib-body"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-page-header"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-bento"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-kpi-total"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-health-panel"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-filter-bar"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-search"]')).toHaveAttribute(
			'placeholder',
			'Search STDs...',
		);
		await expect(page.locator('[data-testid="kt-std-lib-filter-btn"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-create-btn"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-col-method"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-col-actions"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-table"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-pagination"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-pagination-pages"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-lib-pagination-size"]')).toBeVisible();
	});

	test('std-engine redirects to std-library when v2 enabled', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page).toHaveURL(/std-library/i, { timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({
			timeout: 90_000,
		});
	});
});
