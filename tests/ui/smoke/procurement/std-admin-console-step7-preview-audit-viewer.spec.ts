import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	STD_ADMIN_TEMPLATE_CODE,
	clickStdAdminAction,
	clickStdDemoAction,
} from '../../helpers/stdAdminConsoleDesk';

test.describe('STD Administration Console — Step 7 preview and audit viewer (Desk)', () => {
	test.setTimeout(120_000);

	test('Demo workspace shows preview audit block; modal opens from STD Demo', async ({ page }) => {
		await loginAsAdministrator(page);

		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});

		const createResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('create_or_open_std_demo_tender') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);

		await clickStdAdminAction(page, 'Create/Open Demo Tender');
		await createResp;

		await expect(page).toHaveURL(/procurement-tender\//, { timeout: 120_000 });

		await expect(page.locator('.std-admin-preview-audit-viewer')).toBeVisible({ timeout: 120_000 });
		await expect(page.locator('.std-preview-audit-poc-banner')).toContainText('POC preview and audit');

		await clickStdDemoAction(page, 'Preview and audit viewer');
		const dlg = page.locator('.modal-dialog:visible').first();
		await expect(dlg).toBeVisible({ timeout: 120_000 });
		await expect(dlg.locator('.std-admin-preview-audit-viewer')).toBeVisible();
		await dlg.getByRole('button', { name: 'Close', exact: true }).click();
		await expect(dlg).toBeHidden({ timeout: 30_000 });
	});
});
