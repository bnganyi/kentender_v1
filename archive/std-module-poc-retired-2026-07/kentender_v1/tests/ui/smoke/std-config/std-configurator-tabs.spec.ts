/**
 * STD-CFG-0200 — STD Configurator tab shell smoke.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('STD Config UI — Configurator shell (STD-CFG-0200)', () => {
	test.setTimeout(180_000);

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('configurator shell renders tab host', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({
			timeout: 90_000,
		});
		const configureBtn = page.locator('[data-testid="kt-std-lib-configure"]').first();
		if ((await configureBtn.count()) === 0) {
			test.skip(true, 'No editable STD rows in catalogue');
		}
		await configureBtn.click();
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-breadcrumbs"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-doc-header"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-footer-actions"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-identity-card"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-progress-card"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-topbar"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-tab-overview"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-overview"]')).toBeVisible();

		const tabbarMetrics = await page.locator('[data-testid="kt-std-cfg-tabs"]').evaluate((el) => {
			const style = getComputedStyle(el);
			return {
				flexWrap: style.flexWrap,
				overflowX: style.overflowX,
				hasHorizontalOverflow: el.scrollWidth > el.clientWidth + 1,
			};
		});
		expect(tabbarMetrics.flexWrap).toBe('wrap');
		expect(tabbarMetrics.overflowX).not.toBe('auto');
		expect(tabbarMetrics.hasHorizontalOverflow).toBe(false);
	});

	test('tab cycle does not flash loading placeholders', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library`);
		await dismissOptionalDeskModals(page);
		const configureBtn = page.locator('[data-testid="kt-std-lib-configure"]').first();
		if ((await configureBtn.count()) === 0) {
			test.skip(true, 'No editable STD rows in catalogue');
		}
		await configureBtn.click();
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({
			timeout: 90_000,
		});
		for (const tab of ['applicability', 'tender-fields', 'contract-terms']) {
			await page.locator(`[data-testid="kt-std-cfg-tab-${tab}"]`).click();
			await expect(page.locator(`[data-testid="kt-std-cfg-tab-panel-${tab}"]`)).toBeVisible({
				timeout: 30_000,
			});
			await expect(page.locator('[data-testid="kt-std-cfg-footer-actions"]')).toBeVisible();
			await expect(page.locator('[data-testid="kt-std-cfg-loading"]')).toHaveCount(0);
		}
	});
});
