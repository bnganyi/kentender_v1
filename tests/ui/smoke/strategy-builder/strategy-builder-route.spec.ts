import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { ensureTestStrategicPlan, isolatedPlanName, openStrategyBuilder } from '../../helpers/strategyBuilder';

test('Strategy builder deep link opens workspace Structure tab', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await loginAsAdministrator(page);
	await ensureTestStrategicPlan(page, plan);

	await page.goto(`/app/strategy-builder/${plan}`, { waitUntil: 'domcontentloaded' });
	await expect(page).toHaveURL(/strategy-management/);
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible();
});
