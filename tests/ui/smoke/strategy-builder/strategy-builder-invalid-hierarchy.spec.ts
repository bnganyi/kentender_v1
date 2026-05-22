import { test, expect } from '@playwright/test';

import {
	clearStrategyNodes,
	ensureTestStrategicPlan,
	isolatedPlanName,
	openStrategyBuilder,
} from '../../helpers/strategyBuilder';

test('Invalid hierarchy actions are blocked in workspace Structure tab', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	await ensureTestStrategicPlan(page, plan);
	await clearStrategyNodes(page, plan);
	await openStrategyBuilder(page, plan);

	await page.getByTestId('structure-subtab-subprograms').click();
	await expect(page.getByTestId('structure-add-subprogram')).toBeVisible({ timeout: 15_000 });
	await page.getByTestId('structure-add-subprogram').click();
	await expect(page.getByText(/Create the parent level first/i)).toBeVisible({ timeout: 15_000 });
	await page.locator('.modal.show .btn-modal-close, .modal.show .close').first().click();

	await page.getByTestId('structure-subtab-targets').click();
	await expect(page.getByTestId('structure-add-target')).toBeVisible({ timeout: 15_000 });
	await page.getByTestId('structure-add-target').click();
	await expect(page.getByText(/Create the parent level first/i)).toBeVisible({ timeout: 15_000 });
});
