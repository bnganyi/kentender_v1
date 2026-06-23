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

	test('root route renders PP3 Workbench and hides legacy Planning Home surface', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp3-planning-workbench')).toHaveCount(1);
		await expect(page.getByTestId('pp2-planning-home-surface')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-home-queues')).toHaveCount(0);
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible();
		await expect(page.getByTestId('pp3-work-list')).toBeVisible();
		await expect(page.getByTestId('pp3-selected-work-summary')).toBeVisible();
		await expect(page.getByTestId('pp2-page-title')).toHaveText('Workbench');

		await page.screenshot({ path: 'artifacts/p3-001-workbench-route.png', fullPage: true });
	});
});
