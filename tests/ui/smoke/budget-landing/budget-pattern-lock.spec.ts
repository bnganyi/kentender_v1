import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openBudgetLanding } from '../../helpers/budgetLanding';
import {
	expectNoLoadingFlash,
	expectPrimaryTabsUseHierarchyContract,
	expectStatusFiltersUseHierarchyContract,
} from '../../helpers/workspacePatternContract';

test.describe('Budget workspace pattern lock', () => {
	test('budget rail keeps header separated from scrollable list', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);

		await expect(page.getByTestId('budget-list-head')).toBeVisible();
		const list = page.getByTestId('budget-list');
		await expect(list).toBeVisible();
		await expect(list).toHaveCSS('overflow-y', 'scroll');

		const isScrollable = await list.evaluate((el) => el.scrollHeight > el.clientHeight);
		if (isScrollable) {
			await list.evaluate((el) => {
				el.scrollTop = 120;
			});
			await expect
				.poll(async () => list.evaluate((el) => el.scrollTop))
				.toBeGreaterThan(0);
		}
	});

	test('detail pane follows card hierarchy and status guidance is inline', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);

		const panel = page.getByTestId('selected-budget-panel');
		await expect(panel).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('.kt-budget-detail-section')).toHaveCount(1);
		await expect(page.locator('.kt-budget-detail__hero')).toHaveCount(1);
		await expect(page.locator('.kt-budget-detail__stats')).toHaveCount(1);
		await expect(page.locator('.kt-budget-status-guidance')).toHaveCount(1);
		await expect(page.locator('.kt-budget-next-step-inline')).toHaveCount(1);
	});

	test('detail tabs do not flash loading placeholders when switching', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);

		const list = page.getByTestId('budget-list');
		await expect(list).toBeVisible();
		await list.evaluate((el) => {
			el.scrollTop = el.scrollHeight;
		});
		const before = await list.evaluate((el) => el.scrollTop);
		const allocationsTab = page.getByTestId('budget-tab-allocations');
		const allocationsPanel = page.getByTestId('budget-tab-panel-allocations');
		await allocationsTab.click();
		await expect(allocationsPanel).toBeVisible();
		const after = await list.evaluate((el) => el.scrollTop);
		if (before > 0) {
			expect(Math.abs(after - before)).toBeLessThanOrEqual(2);
		}

		const reviewTab = page.getByTestId('budget-tab-review');
		const reviewPanel = page.getByTestId('budget-tab-panel-review');
		await reviewTab.click();
		await expectNoLoadingFlash(reviewPanel, page.getByText('Loading readiness…'));

		const auditTab = page.getByTestId('budget-tab-audit');
		const auditPanel = page.getByTestId('budget-tab-panel-audit');
		await auditTab.click();
		await expectNoLoadingFlash(auditPanel, page.getByText('Loading audit…'));
	});

	test('status filters and primary tabs respect hierarchy contracts', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);

		await expectStatusFiltersUseHierarchyContract(page.getByTestId('budget-status-chips'), {
			allTestId: 'budget-tab-all',
			sampleZeroTestId: 'budget-tab-submitted',
		});
		await page.getByTestId('budget-tab-summary').click();
		await expectPrimaryTabsUseHierarchyContract(page, { tabPrefix: 'budget-tab-' });
	});

	test('audit downstream usage emphasizes metric values', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetLanding(page);
		await page.getByTestId('budget-tab-audit').click();
		await expect(page.getByTestId('budget-tab-panel-audit')).toBeVisible();

		const lines = page.locator('.kt-budget-audit-line');
		test.skip((await lines.count()) === 0, 'Requires downstream usage records in seeded data.');
		const value = lines.first().locator('.kt-budget-audit-line__value');
		await expect(value).toBeVisible();
		const fontWeight = await value.evaluate((el) => window.getComputedStyle(el).fontWeight);
		expect(Number(fontWeight)).toBeGreaterThanOrEqual(600);
	});
});
