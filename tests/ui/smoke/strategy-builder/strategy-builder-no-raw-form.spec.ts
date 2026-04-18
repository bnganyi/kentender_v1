import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
	submitNewNodeDialog,
	treeNodeButton,
} from '../../helpers/strategyBuilder';

test('Builder editing does not navigate to raw forms', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await page.getByTestId('add-program-button').click();
	await submitNewNodeDialog(page, { title: 'Healthcare Delivery' }, /New Program/i);

	await treeNodeButton(page, /Healthcare Delivery/).click();
	await page.getByTestId('node-title-input').fill('Healthcare Delivery Updated');
	await page.getByTestId('save-node-button').click();

	await expect(page).toHaveURL(/strategy-builder/);
	await expect(page.url()).not.toMatch(/strategy-node/);
});
