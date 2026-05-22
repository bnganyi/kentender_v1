import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	seedHierarchyForContract,
} from '../../helpers/strategyBuilder';
import { openStrategyStructureTab } from '../../helpers/strategyWorkbench';

test('Active plan Structure tab is read-only', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await loginAsAdministrator(page);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await seedHierarchyForContract(page, plan);

	await page.evaluate(async (planName: string) => {
		// @ts-expect-error desk global
		await frappe.call({
			method: 'kentender_strategy.api.strategy_workflow.submit_plan',
			args: { plan_name: planName },
		});
		// @ts-expect-error desk global
		await frappe.call({
			method: 'kentender_strategy.api.strategy_workflow.approve_plan',
			args: { plan_name: planName },
		});
		// @ts-expect-error desk global
		await frappe.call({
			method: 'kentender_strategy.api.strategy_workflow.activate_plan',
			args: { plan_name: planName },
		});
	}, plan);

	await openStrategyStructureTab(page, plan);
	await page.getByTestId('structure-subtab-programs').click();
	await expect(page.getByTestId('structure-add-program')).toHaveCount(0);
});
