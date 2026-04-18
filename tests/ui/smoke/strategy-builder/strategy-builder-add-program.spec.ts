import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
	treeNodeButton,
} from '../../helpers/strategyBuilder';

test('Can add Program node', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await page.getByTestId('add-program-button').click();
	await submitNewNodeDialog(
		page,
		{
			title: 'Healthcare Delivery',
			description: 'Top-level program',
		},
		/New Program/i,
	);

	await expect(treeNodeButton(page, /Healthcare Delivery/)).toBeVisible();
	await expect(page).toHaveURL(/strategy-builder/);
	await expect(page.getByTestId('selected-node-type')).toHaveText(/Program/i);
});
