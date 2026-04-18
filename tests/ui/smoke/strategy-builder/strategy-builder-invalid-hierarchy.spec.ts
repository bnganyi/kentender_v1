import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
	treeNodeButton,
} from '../../helpers/strategyBuilder';

test('Invalid hierarchy actions are blocked', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await expect(page.getByTestId('add-objective-button')).toBeDisabled();
	await expect(page.getByTestId('add-target-button')).toBeDisabled();

	await page.getByTestId('add-program-button').click();
	await submitNewNodeDialog(page, { title: 'Healthcare Delivery' }, /New Program/i);

	await treeNodeButton(page, /Healthcare Delivery/).click();
	await expect(page.getByTestId('add-target-button')).toBeDisabled();
});
