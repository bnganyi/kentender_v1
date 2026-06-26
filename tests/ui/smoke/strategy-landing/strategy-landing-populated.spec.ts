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
});

test('Strategy portfolio hub KPI cards render with live data labels', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const metrics = page.getByTestId('sph-metrics-grid');
	await expect(metrics).toContainText('Total Budget');
	await expect(metrics).toContainText('Active Programs');
	await expect(metrics).toContainText('Success Rate');
	await expect(metrics).toContainText('Draft Plans');
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
});

test('Strategy portfolio hub search filters plan cards', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	/* Wait for at least one real card */
	await expect(page.getByTestId('sph-plan-card').first()).toBeVisible({ timeout: 15_000 });

	const search = page.getByTestId('sph-search-input');
	await expect(search).toBeVisible();
	await search.fill('zzznomatch');

	/* All real plan cards should be faded (opacity reduced) */
	const cards = page.getByTestId('sph-plan-card');
	const count = await cards.count();
	if (count > 0) {
		const opacity = await cards.first().evaluate((el) => window.getComputedStyle(el).opacity);
		expect(parseFloat(opacity)).toBeLessThan(1);
	}
});

test('Strategy portfolio hub shows create-new card always', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('sph-create-new-card')).toBeVisible();
	await expect(page.getByTestId('sph-create-plan-btn')).toBeVisible();
});
