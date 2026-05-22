import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { ensureTestStrategicPlan, isolatedPlanName } from '../../helpers/strategyBuilder';
import { openStrategyLanding } from '../../helpers/strategyLanding';
import { saveVisibleDialog, selectStrategicPlan } from '../../helpers/strategyWorkbench';

test('Edit plan metadata in drawer updates workspace header', async ({ page }, testInfo) => {
	const plan = isolatedPlanName(testInfo);
	const updatedTitle = `Updated Plan ${testInfo.parallelIndex}`;

	await loginAsStrategyManager(page);
	await ensureTestStrategicPlan(page, plan);
	await openStrategyLanding(page);
	await selectStrategicPlan(page, plan);

	await page.getByTestId('selected-plan-edit-plan').click();
	const dialog = page.locator('.modal.show').filter({ has: page.getByRole('heading', { name: /Edit Plan Info/i }) });
	await expect(dialog).toBeVisible();
	await dialog.locator('[data-fieldname="strategic_plan_name"] input').fill(updatedTitle);
	await saveVisibleDialog(page);

	await expect(page.getByTestId('selected-plan-title')).toContainText(updatedTitle);
	await expect(page).toHaveURL(/strategy-management/);
});
