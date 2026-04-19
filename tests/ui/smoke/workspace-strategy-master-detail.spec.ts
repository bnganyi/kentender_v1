import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../helpers/auth';
import { ensureStrategicPlanForWorkspace, isolatedPlanName } from '../helpers/strategyBuilder';
import { strategyWorkspace } from '../helpers/selectors';

test('Strategy workspace shows created plans and selected-plan actions', async ({ page }, testInfo) => {
	await loginAsAdministrator(page);

	const docName = isolatedPlanName(testInfo, 'WS-MD');
	const strategicPlanName = `WS MasterDetail w${testInfo.parallelIndex}`;
	await ensureStrategicPlanForWorkspace(page, {
		docName,
		strategic_plan_name: strategicPlanName,
	});

	await page.goto(strategyWorkspace.route);
	await page.waitForLoadState('networkidle');

	await expect(page.getByTestId('strategy-landing-page')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByRole('heading', { name: 'Strategic Plans' })).toBeVisible();
	const planRow = page
		.locator('[data-testid^="strategic-plan-row-"]')
		.filter({ hasText: strategicPlanName });
	await expect(planRow).toBeVisible({ timeout: 60_000 });

	await planRow.click();

	await expect(page.getByTestId('selected-plan-open-builder')).toBeVisible();
	await expect(page.getByTestId('selected-plan-edit-plan')).toBeVisible();
	await expect(page.getByText(/Programs:/i)).toBeVisible();
	await expect(page.getByText(/Objectives:/i)).toBeVisible();
	await expect(page.getByText(/Targets:/i)).toBeVisible();
});
