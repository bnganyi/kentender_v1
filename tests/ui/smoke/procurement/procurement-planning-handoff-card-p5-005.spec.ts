import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';
const seedPackageCode = 'PKG-MOH-2026-001';

test.describe('P5-005 PlanningHandoffCard', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('packages route does not mount handoff cards as default primary content', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages?package_code=${seedPackageCode}`, {
			waitUntil: 'domcontentloaded',
		});

		const mainHost = page.getByTestId('pp2-primary-main-host');
		await expect(mainHost).toBeVisible({ timeout: 60000 });
		await expect(page.getByTestId('pp2-package-handoff-stack')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-handoff-card')).toHaveCount(0);
		await expect(page.getByTestId('pp2-module-journey-context-header')).toHaveCount(0);
		await expect(page.getByTestId('pp2-package-status-strip')).toHaveCount(0);
	});

	test('default packages view does not expose handoff technical details controls', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages?package_code=${seedPackageCode}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(page.getByTestId('pp2-handoff-card-technical-details')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-handoff-technical-toggle')).toHaveCount(0);
	});

	test('planning home route keeps handoff stack absent', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/home`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-main-host')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-package-handoff-stack')).toHaveCount(0);
		await expect(page.locator('body')).not.toContainText(
			/9\.1 shell baseline active|Feature content is intentionally deferred|shell-only baseline active|stub/i
		);
	});
});
