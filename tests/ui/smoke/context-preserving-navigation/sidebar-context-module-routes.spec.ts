import { test, expect } from '@playwright/test';

import { ensureTestStrategicPlan, isolatedPlanName, openStrategyBuilder } from '../../helpers/strategyBuilder';
import { loginAsAdministrator } from '../../helpers/auth';

test('Strategy structure tab keeps Procurement sidebar context', async ({ page }, testInfo) => {
	await loginAsAdministrator(page);
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await openStrategyBuilder(page, plan);

	await expect(page.getByRole('link', { name: 'Procurement Home' })).toBeVisible({ timeout: 30_000 });
	await expect(page.getByRole('link', { name: 'Strategy Alignment' })).toBeVisible({ timeout: 30_000 });
});
