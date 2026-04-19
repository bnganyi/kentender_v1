import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Open Strategy Builder action routes correctly', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('selected-plan-open-builder').click();

	await expect(page).toHaveURL(/strategy-builder/);
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 30_000 });
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
