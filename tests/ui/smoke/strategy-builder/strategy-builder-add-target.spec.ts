import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
	treeNodeButton,
} from '../../helpers/strategyBuilder';

test('Can add Target under Objective', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await page.getByTestId('add-program-button').click();
	await submitNewNodeDialog(page, { title: 'Healthcare Delivery' }, /New Program/i);

	await treeNodeButton(page, /Healthcare Delivery/).click();
	await page.getByTestId('add-objective-button').click();
	await submitNewNodeDialog(page, { title: 'Increase rural access' }, /New Objective/i);

	await treeNodeButton(page, /Increase rural access/).click();
	await expect(page.getByTestId('add-target-button')).toBeEnabled();

	await page.getByTestId('add-target-button').click();
	await submitNewNodeDialog(
		page,
		{
			title: 'Expand district facilities',
			targetYear: '2026',
			targetValue: '25',
			targetUnit: 'Facilities',
		},
		/New Target/i,
	);

	await expect(treeNodeButton(page, /Expand district facilities/)).toBeVisible();
	await expect(page.getByTestId('selected-node-type')).toHaveText(/Target/i);
});
