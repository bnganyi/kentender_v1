import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

/**
 * Assumes the site has **no** Strategic Plan rows (e.g. after `seed_strategy_empty`).
 * Skip or use a dedicated empty site if your default DB is seeded with plans.
 */
test('Strategy landing shows correct empty state when no plans exist', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const planRows = await page.locator('[data-testid^="strategic-plan-row-"]').count();
	test.skip(planRows > 0, 'Site has strategic plans — use an empty site or seed_strategy_empty to assert empty state');

	await expect(page.getByTestId('strategic-plans-section')).toBeVisible();
	await expect(page.getByTestId('strategic-plans-empty-state')).toContainText(
		'No strategic plans yet. Create one to begin.',
	);
	await expect(page.getByTestId('strategic-plan-create-button')).toBeVisible();
	await expect(page.locator('[data-testid^="strategic-plan-row-"]')).toHaveCount(0);
	await expect(page.getByTestId('selected-plan-panel')).toHaveCount(0);
});
