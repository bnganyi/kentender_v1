import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Plan tabs switch without leaving workspace', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);
	await expect(page.getByTestId('selected-plan-panel')).toBeVisible();

	await page.getByTestId('strategy-tab-structure').click();
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible();
	await expect(page).toHaveURL(/strategy-management/);

	await page.getByTestId('strategy-tab-review').click();
	await expect(page.getByTestId('strategy-tab-panel-review')).toBeVisible();

	await page.getByTestId('strategy-tab-audit').click();
	await expect(page.getByTestId('strategy-tab-panel-audit')).toBeVisible();

	await page.getByTestId('strategy-tab-plan-info').click();
	await expect(page.getByTestId('strategy-tab-panel-info')).toBeVisible();
});

test('Manage Structure stays on workspace', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('selected-plan-open-builder').click();
	await expect(page).toHaveURL(/strategy-management/);
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible({ timeout: 30_000 });
});
