import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';
import { saveVisibleDialog } from '../../helpers/strategyWorkbench';

test('Create plan in drawer stays on workspace and selects new row', async ({ page }, testInfo) => {
	const visibleName = `Drawer Create ${testInfo.parallelIndex}`;

	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategic-plan-create-button').click();
	const dialog = page.locator('.modal.show').filter({ has: page.getByRole('heading', { name: /New Strategic Plan/i }) });
	await expect(dialog).toBeVisible();

	await dialog.locator('[data-fieldname="strategic_plan_name"] input').fill(visibleName);
	const entityInput = dialog.locator('[data-fieldname="procuring_entity"] input');
	await entityInput.fill('MOH');
	await entityInput.press('ArrowDown');
	await entityInput.press('Enter');
	await dialog.locator('[data-fieldname="start_year"] input').fill('2026');
	await dialog.locator('[data-fieldname="end_year"] input').fill('2030');

	await saveVisibleDialog(page);

	await expect(page).toHaveURL(/strategy-management/);
	await expect(page.getByTestId('strategic-plan-list')).toContainText(visibleName);
});
