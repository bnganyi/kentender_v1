import { test, expect } from '@playwright/test';

import { ensureTestStrategicPlan, isolatedPlanName, openStrategyBuilder } from '../../helpers/strategyBuilder';

test('Strategy Builder route opens', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await openStrategyBuilder(page, plan);

	await expect(page.getByTestId('strategy-builder-page')).toBeVisible();
	await expect(page.getByTestId('strategy-tree-pane')).toBeVisible();
	await expect(page.getByTestId('strategy-editor-pane')).toBeVisible();
	await expect(page.locator('body')).not.toHaveText(/^$/);
});
