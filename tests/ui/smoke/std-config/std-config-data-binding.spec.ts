/**
 * STD-CFG — Playwright data-bound assertions against UI fixture template.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const FIXTURE_CODE = 'STD-CFG-UI-FIXTURE';

test.describe('STD Config UI — fixture data binding', () => {
	test.setTimeout(180_000);

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('configurator overview shows seeded metadata title', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/overview`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-overview"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-identity-card"]')).toBeVisible({
			timeout: 30_000,
		});
		const titleInput = page.locator('[data-kt-std-field="title"]');
		await expect(titleInput).toHaveValue(/Building Works/i);
	});

	test('library row shows status pill with dot for fixture template', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({ timeout: 90_000 });
		const fixtureRow = page.locator(`[data-template-code="${FIXTURE_CODE}"]`);
		if ((await fixtureRow.count()) === 0) {
			test.skip(true, 'UI fixture template not seeded on site');
		}
		await expect(fixtureRow.locator('[data-testid="kt-std-lib-status-pill"] .kt-std-status-pill__dot')).toBeVisible();
		await expect(fixtureRow.locator('[data-testid="kt-std-lib-row-method"]')).not.toBeEmpty();
	});
});
