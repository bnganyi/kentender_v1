import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	STD_ADMIN_TEMPLATE_CODE,
	clickStdAdminAction,
} from '../../helpers/stdAdminConsoleDesk';

test.describe('STD Administration Console — Step 4 validation and rule trace (Desk)', () => {
	test.setTimeout(120_000);

	test('Validate Package and Trace Primary Sample Rules open HTML dialogs', async ({ page }) => {
		await loginAsAdministrator(page);

		const validateResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('validate_std_package') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);

		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});

		await expect(
			page.locator(`.inner-group-button[data-label="${encodeURIComponent('STD Admin')}"]`).first(),
		).toBeVisible({ timeout: 120_000 });

		await clickStdAdminAction(page, 'Validate Package');
		await validateResp;

		const valDialog = page.locator('.modal-dialog:visible').first();
		await expect(valDialog).toBeVisible({ timeout: 120_000 });
		await expect(valDialog.locator('.std-admin-validation-report')).toBeVisible();
		await expect(valDialog.getByText('Overall status:')).toBeVisible();
		await valDialog.getByRole('button', { name: 'Close', exact: true }).click();
		await expect(valDialog).toBeHidden({ timeout: 30_000 });

		const traceResp = page.waitForResponse(
			(resp) =>
				resp.url().includes('trace_std_rules_for_sample') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 120_000 },
		);

		await clickStdAdminAction(page, 'Trace Primary Sample Rules');
		await traceResp;

		const traceDialog = page.locator('.modal-dialog:visible').first();
		await expect(traceDialog).toBeVisible({ timeout: 120_000 });
		await expect(traceDialog.locator('.std-admin-rule-trace-report')).toBeVisible();
		await expect(traceDialog.getByText(/Trace source:\s*PRIMARY_SAMPLE/)).toBeVisible();
	});
});
