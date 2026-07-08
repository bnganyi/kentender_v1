import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { STD_ADMIN_TEMPLATE_CODE } from '../../helpers/stdAdminConsoleDesk';

test.describe('STD Administration Console — Step 3 package viewer (Desk)', () => {
	test.setTimeout(120_000);

	test('STD Template form shows read-only package viewer HTML', async ({ page }) => {
		await loginAsAdministrator(page);

		const summary = page.waitForResponse(
			(resp) =>
				resp.url().includes('get_template_package_summary') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);

		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});

		await summary;

		const viewer = page.locator('.std-admin-pkg-viewer');
		await expect(viewer).toBeVisible({ timeout: 120_000 });
		await expect(viewer.getByText('POC Administration View')).toBeVisible();
		await expect(viewer.getByRole('heading', { name: 'Package structure (counts)' })).toBeVisible();
	});
});
