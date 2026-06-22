import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';

const PP3_ROUTES = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/releases',
];

test.describe('P1-001 Main Procurement shell preserved', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('planning routes keep procurement rail visible on direct load and hard refresh', async ({ page }) => {
		for (const path of PP3_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible({
				timeout: 30000,
			});
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toBeVisible();
			await expect(page.getByRole('link', { name: 'Evidence & Audit' }).first()).toBeVisible();
			await expect(page.locator('.section-item[title="Procurement Planning"]').first()).toBeVisible();
			await expect(page.getByTestId('pp3-procurement-planning-shell')).toHaveCount(1);

			await page.reload({ waitUntil: 'domcontentloaded' });
			await expect(page.getByRole('link', { name: 'Procurement Home' }).first()).toBeVisible({
				timeout: 30000,
			});
			await expect(page.getByRole('link', { name: 'Procurement Journeys' }).first()).toBeVisible();
			await expect(page.getByRole('link', { name: 'Evidence & Audit' }).first()).toBeVisible();
			await expect(page.locator('.section-item[title="Procurement Planning"]').first()).toBeVisible();
			await expect(page.getByTestId('pp3-procurement-planning-shell')).toHaveCount(1);

			const routeSlug = path.replace('/desk/procurement-planning', '').replace(/\//g, '-') || '-home';
			await page.screenshot({ path: `artifacts/p1-001-shell${routeSlug}.png`, fullPage: true });
		}
	});
});
