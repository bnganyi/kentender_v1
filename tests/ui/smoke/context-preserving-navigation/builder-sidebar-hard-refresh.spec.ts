import { test, expect } from '@playwright/test';

import {
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
} from '../../helpers/strategyBuilder';

test('Strategy workspace Structure tab hard refresh keeps sidebar populated', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await openStrategyBuilder(page, plan);
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible({ timeout: 60_000 });

	await page.reload({ waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('strategy-landing-page')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible({ timeout: 60_000 });

	const navLink = page.getByRole('link', { name: /Strategy Alignment|Budget|Demand Intake/i }).first();
	await expect(navLink).toBeVisible({ timeout: 30_000 });
});
