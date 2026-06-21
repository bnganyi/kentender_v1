/**
 * Regression — PP2 planning shell must not leak into other procurement modules.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

async function clickSidebar(page: import('@playwright/test').Page, label: string) {
	const link = page.locator('.sidebar-item-container').filter({ hasText: label }).first();
	await link.click();
}

test.describe('PP2 shell cross-module containment', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('does not show planning shell on Procurement Home after Planning → DIA → Home', async ({
		page,
	}) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveCount(1, { timeout: 30000 });

		await clickSidebar(page, 'Demand Intake');
		await expect(page).toHaveURL(/demand-intake/i, { timeout: 30000 });

		await clickSidebar(page, 'Procurement Home');
		await expect(page).toHaveURL(/procurement-home/i, { timeout: 30000 });
		await expect(page.getByTestId('ph-landing-page')).toBeVisible({ timeout: 30000 });

		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveCount(0);
		await expect(page.getByTestId('pp2-primary-breadcrumb')).toHaveCount(0);
		await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(0);
	});
});
