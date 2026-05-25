import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';

const PP2_SURFACE_PATHS = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
	'/desk/procurement-planning/evidence',
];

test.describe('P5-002 PrimaryWorkspaceShell', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('renders primary shell frame and right panel toggle', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-primary-breadcrumb')).toBeVisible();
		await expect(page.getByTestId('pp2-primary-context-host')).toBeVisible();
		await expect(page.getByTestId('pp2-primary-main-host')).toBeVisible();
		await expect(page.getByTestId('pp2-primary-right-panel')).toBeVisible();
		const toggle = page.getByTestId('pp2-primary-right-panel-toggle');
		await expect(toggle).toBeVisible();
		await toggle.click();
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveAttribute(
			'data-right-panel-collapsed',
			'1'
		);
		await toggle.click();
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveAttribute(
			'data-right-panel-collapsed',
			'0'
		);
	});

	test('keeps shell chrome stable across all five PP2 routes', async ({ page }) => {
		for (const path of PP2_SURFACE_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
			await expect(page.getByTestId('pp2-primary-breadcrumb')).toBeVisible();
			await expect(page.getByTestId('pp2-primary-right-panel')).toBeVisible();
		}
	});
});
