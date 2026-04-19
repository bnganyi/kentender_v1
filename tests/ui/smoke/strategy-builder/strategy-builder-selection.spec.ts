import { test, expect } from '@playwright/test';

import {
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	seedHierarchyForContract,
	treeNodeButton,
} from '../../helpers/strategyBuilder';

test('Selecting nodes updates editor pane correctly', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await seedHierarchyForContract(page, plan);
	await openStrategyBuilder(page, plan);

	await treeNodeButton(page, /Healthcare Delivery/).click();
	await expect(page.getByTestId('selected-node-type')).toHaveText(/Program/i);

	await treeNodeButton(page, /Increase rural access/).click();
	await expect(page.getByTestId('selected-node-type')).toHaveText(/Objective/i);

	await treeNodeButton(page, /Expand district facilities/).click();
	await expect(page.getByTestId('selected-node-type')).toHaveText(/Target/i);

	await expect(page.getByTestId('target-year-input')).toBeVisible();
	await expect(page.getByTestId('target-value-input')).toBeVisible();
	await expect(page.getByTestId('target-unit-select')).toBeVisible();
});
