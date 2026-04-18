import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
	treeNodeButton,
} from '../../helpers/strategyBuilder';

test('Can add Objective under Program', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await page.getByTestId('add-program-button').click();
	await submitNewNodeDialog(page, { title: 'Healthcare Delivery' }, /New Program/i);
	await expect(treeNodeButton(page, /Healthcare Delivery/)).toBeVisible();

	await treeNodeButton(page, /Healthcare Delivery/).click();
	await expect(page.getByTestId('add-objective-button')).toBeEnabled();

	await page.getByTestId('add-objective-button').click();
	await submitNewNodeDialog(
		page,
		{
			title: 'Increase rural access',
			description: 'Improve services in rural areas',
		},
		/New Objective/i,
	);

	await expect(treeNodeButton(page, /Increase rural access/)).toBeVisible();
	await expect(page.getByTestId('selected-node-type')).toHaveText(/Objective/i);
});
