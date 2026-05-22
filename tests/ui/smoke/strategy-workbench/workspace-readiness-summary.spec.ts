import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

const SEEDED_BASIC_PLAN_TITLE = 'MOH Strategic Plan 2026–2030';

test('Selected plan shows four-level structure counts', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategic-plan-list').getByText(SEEDED_BASIC_PLAN_TITLE).click();

	await expect(page.getByTestId('selected-plan-program-count')).toContainText('2');
	await expect(page.getByTestId('selected-plan-sub-program-count')).toContainText('2');
	await expect(page.getByTestId('selected-plan-indicator-count')).toContainText('3');
	await expect(page.getByTestId('selected-plan-target-count')).toContainText('4');
	await expect(page.getByTestId('selected-plan-readiness')).toBeVisible();
});
