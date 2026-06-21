import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';

const PP2_ROUTES = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
];

test.describe('P5A-002 Procurement shell containment', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('all planning routes keep procurement rail visible on direct load and hard refresh', async ({
		page,
	}) => {
		for (const path of PP2_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible({
				timeout: 30000,
			});
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toBeVisible();
			await expect(page.getByRole('link', { name: 'Evidence & Audit' }).first()).toBeVisible();
			await expect(page.locator('.section-item[title="Procurement Planning"]').first()).toBeVisible();
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible();

			await page.reload({ waitUntil: 'domcontentloaded' });
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible({
				timeout: 30000,
			});
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toBeVisible();
			await expect(page.getByRole('link', { name: 'Evidence & Audit' }).first()).toBeVisible();
			await expect(page.locator('.section-item[title="Procurement Planning"]').first()).toBeVisible();
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible();
		}
	});
});
