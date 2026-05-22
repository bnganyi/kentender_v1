import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';
import { expectListSelectionPreservesScroll, expectNoLoadingFlash } from '../../helpers/workspacePatternContract';

test.describe('Strategy workspace pattern lock', () => {
	test('list selection preserves scroll position', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		const list = page.getByTestId('strategic-plan-list');
		const rows = page.locator('.kt-strategy-plan-row[data-strategy-plan]');
		test.skip((await rows.count()) < 3, 'Requires at least three plans in list.');

		await expectListSelectionPreservesScroll(page, list, rows, (await rows.count()) - 1);
	});

	test('review tab does not flash loading on plan switch', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		const rows = page.locator('.kt-strategy-plan-row[data-strategy-plan]');
		test.skip((await rows.count()) < 3, 'Requires at least three plans in list.');

		await page.getByTestId('strategy-tab-review').click();
		const reviewPanel = page.getByTestId('strategy-tab-panel-review');
		const loading = page.getByText('Loading review…');
		await expectNoLoadingFlash(reviewPanel, loading);

		await page.keyboard.press('Escape').catch(() => {});
		await rows.nth((await rows.count()) - 2).click({ force: true });
		await expectNoLoadingFlash(reviewPanel, loading);
		await expect(reviewPanel).toContainText(/Current state:|Review readiness is temporarily unavailable\./);
	});
});
