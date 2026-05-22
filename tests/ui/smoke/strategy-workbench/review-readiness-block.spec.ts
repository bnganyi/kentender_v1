import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clearStrategyNodes, ensureTestStrategicPlan, isolatedPlanName } from '../../helpers/strategyBuilder';
import { openStrategyReviewTab } from '../../helpers/strategyWorkbench';

test('Incomplete plan cannot submit from Review tab', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await loginAsAdministrator(page);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyReviewTab(page, plan);

	await expect(page.getByTestId('strategy-submit-plan')).toBeDisabled();
	await expect(page.getByTestId('readiness-check-programs')).toBeVisible();
});
