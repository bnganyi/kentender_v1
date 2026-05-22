import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
} from '../../helpers/strategyBuilder';

test('Empty Structure tab shows correct first action', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await expect(page.getByTestId('structure-overview-empty')).toBeVisible();
	await page.getByTestId('structure-subtab-programs').click();
	await expect(page.getByTestId('structure-add-program')).toBeVisible();
});
