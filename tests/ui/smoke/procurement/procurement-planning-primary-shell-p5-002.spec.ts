import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';

const PP2_SURFACE_PATHS = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
];

test.describe('P5-002 PrimaryWorkspaceShell', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('renders primary shell frame and right panel toggle', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-primary-breadcrumb')).toBeVisible();
		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);
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

	test('keeps a single primary shell instance while switching PP2 routes', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		for (const path of PP2_SURFACE_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			const shell = page.getByTestId('pp2-primary-workspace-shell');
			await expect(shell).toBeVisible({ timeout: 30000 });
			await expect(shell).toHaveCount(1);
		}
	});

	test('preserves right panel collapsed state across PP2 route switches', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const shell = page.getByTestId('pp2-primary-workspace-shell');
		const toggle = page.getByTestId('pp2-primary-right-panel-toggle');
		await expect(shell).toHaveAttribute('data-right-panel-collapsed', '0');
		await toggle.click();
		await expect(shell).toHaveAttribute('data-right-panel-collapsed', '1');
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveAttribute(
			'data-right-panel-collapsed',
			'1'
		);
	});

	test('packages route keeps shell but does not mount handoff-heavy default chrome', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);
		await expect(page.getByTestId('pp2-primary-main-host')).toBeVisible();
		await expect(page.getByTestId('pp2-module-journey-context-header')).toHaveCount(0);
		await expect(page.getByTestId('pp2-package-status-strip')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-status-badge')).toHaveCount(0);
		await expect(page.getByTestId('pp2-package-handoff-stack')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-handoff-card')).toHaveCount(0);
		await expect(page.getByTestId('pp2-primary-next-action-panel')).not.toContainText(
			/Shell-only baseline active|Detailed planning content is intentionally disabled/i
		);
		await expect(page.locator('body')).not.toContainText(
			/9\.1 shell baseline active|Feature content is intentionally deferred|shell-only baseline active|stub/i
		);
	});
});
