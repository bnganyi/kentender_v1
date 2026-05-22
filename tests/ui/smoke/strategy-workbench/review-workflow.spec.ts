import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	seedHierarchyForContract,
} from '../../helpers/strategyBuilder';
import { openStrategyReviewTab } from '../../helpers/strategyWorkbench';

test('Plan moves Draft → Submitted → Approved → Active from Review tab', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await loginAsAdministrator(page);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await seedHierarchyForContract(page, plan);
	await openStrategyReviewTab(page, plan);

	await expect(page.getByTestId('strategy-submit-plan')).toBeEnabled();
	await Promise.all([
		page.waitForResponse(
			(r) => r.url().includes('kentender_strategy.api.strategy_workflow.submit_plan') && r.ok(),
			{ timeout: 60_000 },
		),
		page.getByTestId('strategy-submit-plan').click(),
	]);
	await expect(page.getByTestId('strategy-review-status')).toContainText('Submitted', { timeout: 30_000 });

	await Promise.all([
		page.waitForResponse(
			(r) => r.url().includes('kentender_strategy.api.strategy_workflow.approve_plan') && r.ok(),
			{ timeout: 60_000 },
		),
		page.getByTestId('strategy-approve-plan').click(),
	]);
	await expect(page.getByTestId('strategy-review-status')).toContainText('Approved', { timeout: 30_000 });

	await Promise.all([
		page.waitForResponse(
			(r) => r.url().includes('kentender_strategy.api.strategy_workflow.activate_plan') && r.ok(),
			{ timeout: 60_000 },
		),
		page.getByTestId('strategy-activate-plan').click(),
	]);
	await expect(page.getByTestId('strategy-review-status')).toContainText('Active', { timeout: 30_000 });
});
