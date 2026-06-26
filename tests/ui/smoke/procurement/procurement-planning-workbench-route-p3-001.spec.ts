/**
 * P3-001 — Root route opens PP3 Workbench surface.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

test.describe('P3-001 Workbench route', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('root route renders PP4 Workbench with high-fidelity regions', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp4-workbench')).toHaveCount(1);
		await expect(page.getByTestId('pp4-topbar')).toBeVisible();
		await expect(page.getByTestId('pp4-breadcrumbs')).toBeVisible();
		await expect(page.getByTestId('pp4-stats-grid')).toBeVisible();
		await expect(page.getByTestId('pp4-work-queue-tabs')).toBeVisible();
		await expect(page.getByTestId('pp4-package-grid')).toBeVisible();
		await expect(page.getByTestId('pp4-create-package-card')).toBeVisible();
		await expect(page.getByTestId('pp4-topbar-search')).toBeVisible();
		await expect(page.getByText('End-to-End Procurement Planning')).toBeVisible();
		await expect(page.getByText('PKG-MOH-2026-001')).toBeVisible();

		await page.screenshot({ path: 'artifacts/p3-001-workbench-route.png', fullPage: true });
	});
});
