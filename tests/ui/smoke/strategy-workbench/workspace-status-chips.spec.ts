import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Strategy workspace shows status filter chips', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('strategy-status-chips')).toBeVisible();
	await expect(page.getByTestId('strategy-status-all')).toBeVisible();
	await expect(page.getByTestId('strategy-status-draft')).toBeVisible();
	await expect(page.getByTestId('strategy-status-active')).toBeVisible();
});

test('Status chip filters plan list', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategy-status-draft').click();
	await expect(page.getByTestId('strategic-plan-list').or(page.getByTestId('strategic-plans-filter-empty'))).toBeVisible();
});
