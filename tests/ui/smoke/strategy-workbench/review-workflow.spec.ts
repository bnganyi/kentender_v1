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
	await expect(page.getByTestId(`strategic-plan-row-${plan}`)).toContainText(/Submitted/i, { timeout: 30_000 });

	await Promise.all([
		page.waitForResponse(
			(r) => r.url().includes('kentender_strategy.api.strategy_workflow.approve_plan') && r.ok(),
			{ timeout: 60_000 },
		),
		page.getByTestId('strategy-approve-plan').click(),
	]);
	await expect(page.getByTestId('strategy-review-status')).toContainText('Approved', { timeout: 30_000 });
	await expect(page.getByTestId(`strategic-plan-row-${plan}`)).toContainText(/Approved/i, { timeout: 30_000 });

	await Promise.all([
		page.waitForResponse(
			(r) => r.url().includes('kentender_strategy.api.strategy_workflow.activate_plan') && r.ok(),
			{ timeout: 60_000 },
		),
		page.getByTestId('strategy-activate-plan').click(),
	]);
	await expect(page.getByTestId('strategy-review-status')).toContainText('Active', { timeout: 30_000 });
	await expect(page.getByTestId(`strategic-plan-row-${plan}`)).toContainText(/Active/i, { timeout: 30_000 });
});

test('Review action buttons have visible spacing', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await loginAsAdministrator(page);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await seedHierarchyForContract(page, plan);
	await openStrategyReviewTab(page, plan);

	await Promise.all([
		page.waitForResponse(
			(r) => r.url().includes('kentender_strategy.api.strategy_workflow.submit_plan') && r.ok(),
			{ timeout: 60_000 },
		),
		page.getByTestId('strategy-submit-plan').click(),
	]);
	await expect(page.getByTestId('strategy-review-status')).toContainText('Submitted', { timeout: 30_000 });

	const gap = await page.evaluate(() => {
		const wrap = document.querySelector('[data-testid="strategy-review-actions"]');
		if (!wrap) return null;
		const buttons = Array.from(wrap.querySelectorAll('button'));
		if (buttons.length < 2) return null;
		const a = buttons[0].getBoundingClientRect();
		const b = buttons[1].getBoundingClientRect();
		return Math.round(b.left - a.right);
	});
	expect(gap).not.toBeNull();
	expect(gap as number).toBeGreaterThanOrEqual(6);
});
