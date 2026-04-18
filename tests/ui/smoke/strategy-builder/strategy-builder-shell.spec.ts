import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
} from '../../helpers/strategyBuilder';

test('Empty Strategy Builder shows correct first action', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await expect(page.getByTestId('empty-tree-message')).toBeVisible();
	await expect(page.getByTestId('add-program-button')).toBeVisible();
	await expect(page.getByTestId('add-objective-button')).toBeDisabled();
	await expect(page.getByTestId('add-target-button')).toBeDisabled();
});
