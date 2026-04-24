import { test, expect } from '@playwright/test';

import { loginAsAdministrator, loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Open Strategy Builder action routes correctly', async ({ page }) => {
	// Administrator: Strategy Manager Desk session can fail to boot the builder page script
	// (blank main area while URL matches); route + shell are still validated here.
	await loginAsAdministrator(page);
	await openStrategyLanding(page);

	await page.getByTestId('selected-plan-open-builder').click();

	await expect(page).toHaveURL(/strategy-builder/);
	await page.waitForLoadState('networkidle');
	await expect(page.getByTestId('strategy-tree-pane')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 15_000 });
});

test('Edit Plan action routes correctly', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('selected-plan-edit-plan').click();

	await expect(page).toHaveURL(/strategic-plan/);
	await expect(page.getByText(/Strategic Plan/i).first()).toBeVisible();
});

test('New Strategic Plan action opens create form', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategic-plan-create-button').click();

	await expect(page).toHaveURL(/strategic-plan.*new|new.*strategic-plan/i);
	await expect(page.getByText(/Strategic Plan Name/i)).toBeVisible();
});
