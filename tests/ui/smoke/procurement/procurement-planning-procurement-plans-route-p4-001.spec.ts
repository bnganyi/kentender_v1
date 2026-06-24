/**
 * P4-001 — Procurement Plans route opens setup/oversight surface.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

test.describe('P4-001 Procurement Plans route', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('plans route renders PP3 setup/oversight surface without workbench chrome', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp3-procurement-plans-page')).toHaveCount(1);
		await expect(page.getByTestId('pp2-page-title')).toHaveText('Procurement Plans', { timeout: 30000 });
		await expect(page.getByTestId('pp2-page-purpose')).toContainText(
			'Create, activate, and review procurement plans.',
		);
		await expect(page.getByTestId('pp2-planning-home-surface')).toHaveCount(0);
		await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp2-work-list')).toHaveCount(0);
		await expect(page.getByTestId('pp3-work-list')).toHaveCount(0);
		await expect(page.getByTestId('pp3-active-plan-banner')).toHaveCount(0);

		await page.screenshot({ path: 'artifacts/p4-001-procurement-plans-route.png', fullPage: true });
	});
});
