import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

/**
 * Strategic Portfolio Hub smoke tests — live backend wiring.
 * Requires site with at least one Strategic Plan (seed_works_master_strategy_hierarchy).
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
	await expect(page.getByTestId('sph-activity-table')).toBeVisible();
	await expect(page.getByTestId('sph-create-new-card')).toBeVisible();

	/* Activity table must populate with live rows — not the stub text */
	const activityTable = page.getByTestId('sph-activity-table');
	await expect(activityTable).not.toContainText('Activity feed pending wiring', { timeout: 20_000 });
	await expect(activityTable).not.toContainText('Loading activity', { timeout: 20_000 });
	/* At least one row with a recognisable action label */
	const firstRow = activityTable.locator('tbody tr').first();
	await expect(firstRow).toBeVisible({ timeout: 15_000 });
	await expect(firstRow.locator('.kt-sph-action-label')).not.toBeEmpty();
});

test('Strategy portfolio hub KPI cards render with live data labels', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const metrics = page.getByTestId('sph-metrics-grid');
	await expect(metrics).toContainText('Total Budget');
	await expect(metrics).toContainText('Active Programs');
	await expect(metrics).toContainText('Success Rate');
	await expect(metrics).toContainText('Draft Plans');

	/* Total Budget must not show the old stub text — it is now either a value or "No linked demands yet" */
	await expect(metrics).not.toContainText('Pending field configuration');
	/* Success Rate: new weighted-hierarchy label must appear, not old demand-approval stub */
	await expect(metrics).not.toContainText('Pending target completion data', { timeout: 15_000 });
	await expect(metrics).not.toContainText('Of linked demands approved', { timeout: 15_000 });
	await expect(metrics).toContainText('Weighted achievement across active plans', { timeout: 15_000 });
	/* Data coverage sub-text rendered alongside the success rate card */
	await expect(metrics).toContainText('Data coverage:', { timeout: 15_000 });
});

test('Strategy portfolio hub plan cards load from API', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	/* Wait for the API to populate cards (skeleton replaced by real cards) */
	const firstCard = page.getByTestId('sph-plan-card').first();
	await expect(firstCard).toBeVisible({ timeout: 15_000 });

	/* Each card must show a title, a status chip, and at least one stat */
	await expect(firstCard.locator('.kt-sph-card-title')).not.toBeEmpty();
	await expect(firstCard.locator('.kt-sph-chip')).toBeVisible();
	await expect(firstCard.locator('.kt-sph-stat')).toHaveCount(3);

	/* Budget stat must show a live value or "—" (not a placeholder/stub text) */
	const budgetStat = firstCard.locator('.kt-sph-stat').first();
	await expect(budgetStat).toContainText('Budget');
	await expect(budgetStat).not.toContainText('Pending');
});

test('Strategy portfolio hub search filters plan cards', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	/* Wait for at least one real card */
	await expect(page.getByTestId('sph-plan-card').first()).toBeVisible({ timeout: 15_000 });

	const search = page.getByTestId('sph-search-input');
	await expect(search).toBeVisible();

	/* Typing a term that matches nothing should leave only the empty-state card */
	await search.fill('zzznomatch');
	await expect(page.getByTestId('sph-plan-card')).toHaveCount(0);
	await expect(page.getByTestId('sph-create-new-card')).toBeVisible();

	/* Clearing restores all cards */
	await search.fill('');
	await expect(page.getByTestId('sph-plan-card').first()).toBeVisible();
});

test('Strategy portfolio hub shows create-new card always', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('sph-create-new-card')).toBeVisible();
	await expect(page.getByTestId('sph-create-plan-btn')).toBeVisible();
});
