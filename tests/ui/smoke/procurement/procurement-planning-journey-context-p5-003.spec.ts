import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';
const seedPackageCode = 'PKG-MOH-2026-001';

test.describe('P5-003 ModuleJourneyContextHeader', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('does not render journey context header by default on packages route', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages?package_code=${seedPackageCode}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);
		await expect(page.getByTestId('pp2-module-journey-context-header')).toHaveCount(0);
		await expect(page.getByTestId('pp2-module-journey-title')).toHaveCount(0);
		await expect(page.getByTestId('pp2-module-journey-state-line')).toHaveCount(0);
		await expect(page.getByTestId('pp2-module-journey-open')).toHaveCount(0);
	});

	test('does not render journey context header by default on planning home route', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-context-host')).toHaveCount(1);
		await expect(page.getByTestId('pp2-module-journey-context-header')).toHaveCount(0);
		await expect(page.getByTestId('pp2-module-journey-technical-details')).toHaveCount(0);
		await expect(page.getByTestId('pp2-module-journey-technical-toggle')).toHaveCount(0);
	});
});
