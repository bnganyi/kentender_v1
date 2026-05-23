import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openBudgetLanding, waitForFrappeBoot } from '../../helpers/budgetLanding';

test.describe('Budget allocations tab', () => {
	test('Approved budget shows read-only allocations table with footer', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);
		await waitForFrappeBoot(page);

		const approvedRow = page.locator('.kt-budget-row').filter({ hasText: 'BUDGET-MOH-2026' }).first();
		const rowCount = await approvedRow.count();
		test.skip(rowCount === 0, 'Requires WORKS master seed budget BUDGET-MOH-2026');

		await approvedRow.click();
		await page.getByTestId('budget-tab-allocations').click();
		await expect(page.getByTestId('budget-allocations-readonly-banner')).toBeVisible({ timeout: 30_000 });
		await expect(page.getByTestId('budget-allocations-table')).toBeVisible();
		await expect(page.getByTestId('budget-allocation-add')).toHaveCount(0);
		await expect(page.getByTestId('budget-allocations-footer')).toContainText('Total allocated');
	});

	test('Approved allocation row opens read-only drawer', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);
		await waitForFrappeBoot(page);

		const approvedRow = page.locator('.kt-budget-row').filter({ hasText: 'BUDGET-MOH-2026' }).first();
		test.skip((await approvedRow.count()) === 0, 'Requires WORKS master seed budget BUDGET-MOH-2026');

		await approvedRow.click();
		await page.getByTestId('budget-tab-allocations').click();
		const lineRow = page
			.locator('[data-testid^="budget-allocation-row-"]')
			.filter({ hasText: 'District Health Facility Infrastructure Rehabilitation' })
			.first();
	await expect(lineRow).toBeVisible({ timeout: 30_000 });
	await lineRow.getByRole('button', { name: 'View' }).click();
		await expect(page.getByTestId('budget-allocation-drawer')).toBeVisible({ timeout: 15_000 });
	});
});
