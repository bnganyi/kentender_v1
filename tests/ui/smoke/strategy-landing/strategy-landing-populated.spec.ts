import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

/** From seed_strategy_basic / seed spec (MOH). */
const SEEDED_BASIC_PLAN_TITLE = 'MOH Strategic Plan 2026–2030';

/**
 * Assumes `seed_core_minimal` + `seed_strategy_basic` (or extended) has been applied.
 */
test('Strategy landing shows seeded plans when plans exist', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('strategic-plan-list')).toBeVisible();
	await expect(page.getByText(SEEDED_BASIC_PLAN_TITLE)).toBeVisible();
	await expect(page.getByTestId('strategic-plans-empty-state')).toHaveCount(0);
	await expect(page.getByTestId('selected-plan-panel')).toBeVisible();
	await expect(page.getByTestId('selected-plan-title')).toBeVisible();
	await expect(page.getByTestId('selected-plan-program-count')).toBeVisible();
	await expect(page.getByTestId('selected-plan-objective-count')).toBeVisible();
	await expect(page.getByTestId('selected-plan-target-count')).toBeVisible();
});

test('Selected plan shows correct seeded counts for basic plan', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategic-plan-list').getByText(SEEDED_BASIC_PLAN_TITLE).click();

	await expect(page.getByTestId('selected-plan-title')).toContainText(SEEDED_BASIC_PLAN_TITLE);
	await expect(page.getByTestId('selected-plan-program-count')).toContainText('2');
	await expect(page.getByTestId('selected-plan-objective-count')).toContainText('3');
	await expect(page.getByTestId('selected-plan-target-count')).toContainText('4');
});
