/**
 * P2-005 — WorkbenchQueueTabs renders six PP3 queues on Workbench route.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

test.describe('P2-005 WorkbenchQueueTabs', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders exactly six PP3 workbench queue tabs', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const tabs = page.getByTestId('pp3-workbench-queue-tabs');
		await expect(tabs).toBeVisible({ timeout: 30000 });
		await expect(tabs.getByRole('tab')).toHaveCount(6);
		await expect(page.getByTestId('pp3-queue-needs-planning')).toBeVisible();
		await expect(page.getByTestId('pp3-queue-draft-packages')).toBeVisible();
		await expect(page.getByTestId('pp3-queue-needs-review')).toBeVisible();
		await expect(page.getByTestId('pp3-queue-ready-release')).toBeVisible();
		await expect(page.getByTestId('pp3-queue-blocked')).toBeVisible();
		await expect(page.getByTestId('pp3-queue-recently-released')).toBeVisible();
		await page.screenshot({ path: 'artifacts/p2-005-workbench-queue-tabs.png', fullPage: true });
	});

	test('queue tab click syncs PP3 queue key to URL', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible({ timeout: 30000 });
		await page.getByTestId('pp3-queue-draft-packages').click();
		await expect(page).toHaveURL(/queue=draft_packages/, { timeout: 30000 });
	});
});
