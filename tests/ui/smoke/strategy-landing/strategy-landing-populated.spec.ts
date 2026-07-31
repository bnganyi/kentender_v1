import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

/**
 * Strategic Portfolio Hub smoke — Stitch layout
 * (docs/misc/strategy_management_home_code.html).
 */
test('Strategy landing shows portfolio hub shell', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('strategy-portfolio-hub')).toBeVisible();
	await expect(page.getByTestId('sph-topbar')).toBeVisible();
	await expect(page.getByTestId('sph-page-title')).toBeVisible();
	await expect(page.getByTestId('sph-page-title')).toContainText('Strategy Management');
	await expect(page.getByTestId('sph-metrics-grid')).toBeVisible();
	await expect(page.getByTestId('sph-plans-grid')).toBeVisible();
	await expect(page.getByTestId('sph-canvas')).toBeVisible();
	await expect(page.getByTestId('sph-main')).toBeVisible();
	await expect(page.getByTestId('sph-aside')).toBeVisible();
	await expect(page.getByTestId('sph-activity-table')).toBeVisible();
	await expect(page.getByTestId('sph-activity-heading')).toHaveText(/Lineage Activity/i);

	/* Activity rail must populate with live items — not stub text */
	const activity = page.getByTestId('sph-activity-table');
	await expect(activity).not.toContainText('Activity feed pending wiring', { timeout: 20_000 });
	await expect(activity).not.toContainText('Loading activity', { timeout: 20_000 });
	const firstItem = activity.getByTestId('sph-activity-item').first();
	await expect(firstItem).toBeVisible({ timeout: 15_000 });
	await expect(firstItem.locator('.kt-sph-action-label')).not.toBeEmpty();
});

test('Strategy portfolio hub KPI cards render with live data labels', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const metrics = page.getByTestId('sph-metrics-grid');
	await expect(metrics).toContainText('Total Budget');
	await expect(metrics).toContainText('Active Programs');
	await expect(metrics).toContainText('Success Rate');
	await expect(metrics).toContainText('Draft Plans');

	await expect(metrics).not.toContainText('Pending field configuration');
	await expect(metrics).not.toContainText('Pending target completion data', { timeout: 15_000 });
	await expect(metrics).not.toContainText('Of linked demands approved', { timeout: 15_000 });
	await expect(metrics).toContainText('Weighted achievement', { timeout: 15_000 });
});

test('Strategy portfolio hub plan cards load from API', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const firstCard = page.getByTestId('sph-plan-card').first();
	await expect(firstCard).toBeVisible({ timeout: 15_000 });

	await expect(firstCard.locator('.kt-sph-card-title')).not.toBeEmpty();
	await expect(firstCard.locator('.kt-sph-chip')).toBeVisible();
	await expect(firstCard.locator('.kt-sph-stat')).toHaveCount(3);

	const budgetStat = firstCard.locator('.kt-sph-stat').first();
	await expect(budgetStat).toContainText('Budget');
	await expect(budgetStat).not.toContainText('Pending');
});

test('Strategy portfolio hub search filters plan cards', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('sph-plan-card').first()).toBeVisible({ timeout: 15_000 });

	const search = page.getByTestId('sph-search-input');
	await expect(search).toBeVisible();

	await search.fill('zzznomatch');
	await expect(page.getByTestId('sph-plan-card')).toHaveCount(0);
	await expect(page.getByTestId('sph-create-new-card')).toBeVisible();

	await search.fill('');
	await expect(page.getByTestId('sph-plan-card').first()).toBeVisible();
});

test('Strategy portfolio hub create plan control is visible', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('sph-create-plan-btn')).toBeVisible();
});
