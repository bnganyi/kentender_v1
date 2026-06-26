import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

/**
 * Strategic Portfolio Hub smoke tests.
 * Static render — no backend seed required.
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
});

test('Strategy portfolio hub shows plan cards with correct data', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const planCards = page.getByTestId('sph-plan-card');
	await expect(planCards).toHaveCount(3);

	await expect(planCards.nth(0)).toContainText('Ministry of Health 2026-2030');
	await expect(planCards.nth(0)).toContainText('Active');
	await expect(planCards.nth(0)).toContainText('$450M');

	await expect(planCards.nth(1)).toContainText('Digital Health Roadmap');
	await expect(planCards.nth(1)).toContainText('Draft');

	await expect(planCards.nth(2)).toContainText('Infrastructure Renewal Phase II');
});

test('Strategy portfolio hub shows topbar search and metrics', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('sph-search-input')).toBeVisible();
	await expect(page.getByTestId('sph-metrics-grid')).toContainText('Total Budget');
	await expect(page.getByTestId('sph-metrics-grid')).toContainText('Active Programs');
	await expect(page.getByTestId('sph-metrics-grid')).toContainText('Success Rate');
	await expect(page.getByTestId('sph-metrics-grid')).toContainText('Draft Plans');
	await expect(page.getByTestId('sph-create-plan-btn')).toBeVisible();
});

test('Strategy portfolio hub activity table shows lineage entries', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const table = page.getByTestId('sph-activity-table');
	await expect(table).toContainText('New Objective Added');
	await expect(table).toContainText('Budget Re-allocated');
	await expect(table).toContainText('Plan Finalized');
	await expect(table).toContainText('Sarah Chen');
});
