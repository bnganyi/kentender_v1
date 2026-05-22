import { test, expect } from '@playwright/test';

import { loginAsAdministrator, loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';
import {
	expectContextActionUsesHierarchyContract,
	expectDetailTabSwitchPreservesListScroll,
	expectListSelectionPreservesScroll,
	expectNoLoadingFlash,
	expectPrimarySidebarItemHighlighted,
	expectPrimaryTabsUseHierarchyContract,
	expectReviewStatusMatchesWorkspace,
	expectRowActionUsesHierarchyContract,
	expectSearchKeepsFocusWhileTyping,
	expectSecondaryTabsUseHierarchyContract,
	expectStatusFiltersUseHierarchyContract,
	expectStructureOverviewTypographyHierarchy,
} from '../../helpers/workspacePatternContract';

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

	test('search keeps focus while typing', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		const search = page.getByTestId('strategic-plan-search');
		await expectSearchKeepsFocusWhileTyping(search, 'up');
	});

	test('detail tab switch preserves list scroll position', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		const list = page.getByTestId('strategic-plan-list');
		const reviewTab = page.getByTestId('strategy-tab-review');
		const reviewPanel = page.getByTestId('strategy-tab-panel-review');
		await expectDetailTabSwitchPreservesListScroll(list, reviewTab, reviewPanel);
	});

	test('sidebar highlights Strategy Alignment as active item', async ({ page }) => {
		await loginAsAdministrator(page);
		await openStrategyLanding(page);

		await expectPrimarySidebarItemHighlighted(page, 'Strategy Alignment', 'Strategy Alignment (full)');
	});

	test('status filters use visual hierarchy contract', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		await expectStatusFiltersUseHierarchyContract(page.getByTestId('strategy-status-chips'));
	});

	test('primary and secondary tabs use visual hierarchy contract', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		await page.getByTestId('strategy-tab-structure').click();
		await expectPrimaryTabsUseHierarchyContract(page);
		await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible();

		await expect(page.locator('[data-testid="strategy-tab-panel-structure"]:visible')).toBeVisible({
			timeout: 30000,
		});
		const targetsSubtab = page.getByTestId('structure-subtab-targets').last();
		test.skip((await targetsSubtab.count()) === 0, 'Requires loaded structure panel subtabs.');
		await targetsSubtab.click();
		await expectSecondaryTabsUseHierarchyContract(page);
	});

	test('structure actions use contextual and row-action hierarchy contract', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openStrategyLanding(page);

		await page.getByTestId('strategy-tab-structure').click();
		await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible();
		await expect(page.locator('[data-testid="strategy-tab-panel-structure"]:visible')).toBeVisible({
			timeout: 30000,
		});
		const targetsSubtab = page.getByTestId('structure-subtab-targets').last();
		test.skip((await targetsSubtab.count()) === 0, 'Requires loaded structure panel subtabs.');
		await targetsSubtab.click();
		test.skip((await page.getByTestId('structure-add-target').count()) === 0, 'Requires writable Targets context action.');
		test.skip((await page.locator('[data-testid^="structure-edit-"]').count()) === 0, 'Requires at least one target row.');

		await expectContextActionUsesHierarchyContract(page);
		await expectRowActionUsesHierarchyContract(page);
	});

	test('review status stays synced with detail and list statuses', async ({ page }) => {
		await loginAsAdministrator(page);
		await openStrategyLanding(page);
		await page.getByTestId('strategy-tab-review').click();
		await expect(page.getByTestId('strategy-tab-panel-review')).toBeVisible();

		await expectReviewStatusMatchesWorkspace(page);
	});

	test('structure overview applies token and typography hierarchy', async ({ page }) => {
		await loginAsAdministrator(page);
		await openStrategyLanding(page);
		await expectStructureOverviewTypographyHierarchy(page);
	});
});
