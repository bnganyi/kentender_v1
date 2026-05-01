import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	STD_ADMIN_TEMPLATE_CODE,
	clickStdAdminAction,
	clickStdDemoAction,
} from '../../helpers/stdAdminConsoleDesk';

test.describe('STD Administration Console — Step 5 demo workspace (Desk)', () => {
	test.setTimeout(120_000);

	test('Create/Open Demo Tender shows workspace banner and Trace Current Rules dialog', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(
			page.locator(`.inner-group-button[data-label="${encodeURIComponent('STD Admin')}"]`).first(),
		).toBeVisible({ timeout: 120_000 });

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
		await expect(page.locator('.std-demo-workspace-banner')).toBeVisible({ timeout: 120_000 });
		await expect(page.locator('.std-demo-workspace-banner')).toContainText('POC Demo Workspace');
		await expect(page.locator('.std-admin-demo-workspace')).toContainText('Current state summary');

		const traceResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('trace_std_rules_for_tender') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);

		await clickStdDemoAction(page, 'Trace Current Rules');
		await traceResp;

		const traceDialog = page.locator('.modal-dialog:visible').first();
		await expect(traceDialog).toBeVisible({ timeout: 120_000 });
		await expect(traceDialog.getByText(/Trace source:\s*DEMO_TENDER/)).toBeVisible();
		await traceDialog.getByRole('button', { name: 'Close', exact: true }).click();
		await expect(traceDialog).toBeHidden({ timeout: 30_000 });
	});
});
