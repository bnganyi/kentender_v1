import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

const EXTENDED_PLAN_TITLE = 'MOH Service Delivery Improvement Plan 2027–2031';

/**
 * Selection tests require the old master-detail list rail.
 * Skipped pending per-plan workbench rewire.
 */
test('Strategy landing auto-selects a plan by default', async ({ page }) => {
	test.skip(true, 'Requires master-detail list shell — pending per-plan workbench rewire');
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('selected-plan-panel')).toBeVisible();
	const firstRowTitle = page
		.locator('[data-testid="strategic-plan-list"] [data-testid^="strategic-plan-row-title-"]')
		.first();
	await expect(firstRowTitle).toBeVisible();
	await expect(page.getByTestId('selected-plan-title')).toHaveText((await firstRowTitle.innerText()).trim());
});

test('Selecting another plan updates the detail panel', async ({ page }) => {
	test.skip(true, 'Requires master-detail list shell — pending per-plan workbench rewire');
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const extended = page.getByTestId('strategic-plan-list').getByText(EXTENDED_PLAN_TITLE);
	test.skip(
		(await extended.count()) === 0,
		'Requires seed_strategy_extended (second strategic plan).',
	);
	await extended.click();

	await expect(page.getByTestId('selected-plan-title')).toContainText(EXTENDED_PLAN_TITLE);
});

test('Review tab renders panel container', async ({ page }) => {
	test.skip(true, 'Requires per-plan workbench tabs — pending workbench rewire');
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategy-tab-review').click();
	await expect(page.getByTestId('strategy-tab-panel-review')).toBeVisible();
});
