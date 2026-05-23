import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openBudgetLanding, waitForFrappeBoot } from '../../helpers/budgetLanding';

test('Approved budget shows allocations table and drawer on Review landing', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);
	await waitForFrappeBoot(page);

	const approvedRow = page.locator('.kt-budget-row').filter({ hasText: 'BUDGET-MOH-2026' }).first();
	const rowCount = await approvedRow.count();
	test.skip(rowCount === 0, 'Requires WORKS master seed budget BUDGET-MOH-2026');

	await approvedRow.click();
	await expect(page.getByTestId('budget-builder-readonly-banner')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('budget-builder-readonly-banner')).toContainText('approved and locked');
	await page.getByTestId('budget-tab-allocations').click();
	await expect(page.getByTestId('budget-allocations-table')).toBeVisible();
	await expect(page.getByTestId('selected-budget-total')).toContainText('120,000,000.00');
	await expect(page.getByTestId('budget-builder-available')).toHaveCount(0);
	await expect(page.getByTestId('budget-builder-reserved')).toHaveCount(0);
	await expect(page.getByTestId('plc-budget-procurement-use-journeys')).toHaveCount(0);

	const lineRow = page
		.locator('[data-testid^="budget-allocation-row-"]')
		.filter({ hasText: 'District Health Facility Infrastructure Rehabilitation' })
		.first();
	await expect(lineRow).toBeVisible();
	await lineRow.getByRole('button', { name: 'View' }).click();
	await expect(page.getByTestId('budget-allocation-drawer')).toBeVisible({ timeout: 15_000 });
});
