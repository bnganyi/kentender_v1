/**
 * Header wiring smoke — plan title, breadcrumb, status chip, KPI cards
 * all hydrated from get_plan_meta after shell renders.
 */
import { test, expect } from '@playwright/test';

import { loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

async function navigateToFirstPlan(page: import('@playwright/test').Page) {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const firstCard = page.getByTestId('sph-plan-card').first();
	await expect(firstCard).toBeVisible({ timeout: 15_000 });

	const planName = await firstCard.getAttribute('data-plan-name');
	await firstCard.locator('.kt-sph-card-title').first().click();

	await expect(page).toHaveURL(/strategy-builder/, { timeout: 15_000 });
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 20_000 });

	return planName || '';
}

test('Workbench header shows real plan title (not placeholder)', async ({ page }) => {
	await navigateToFirstPlan(page);

	const title = page.locator('[data-swb="page-title"]');
	await expect(title).toBeVisible({ timeout: 10_000 });
	/* Must not still show the "Loading…" placeholder */
	await expect(title).not.toHaveText('Loading…');
	/* Must have some non-empty text */
	const text = await title.textContent();
	expect(text && text.trim().length).toBeGreaterThan(0);
});

test('Workbench header breadcrumb shows entity name', async ({ page }) => {
	await navigateToFirstPlan(page);

	const crumbEntity = page.locator('[data-swb="crumb-entity"]');
	await expect(crumbEntity).toBeVisible({ timeout: 10_000 });
	await expect(crumbEntity).not.toHaveText('All Strategic Plans');

	const crumbPlan = page.locator('[data-swb="crumb-plan"]');
	await expect(crumbPlan).not.toHaveText('Loading…');
});

test('Workbench header status chip shows plan status', async ({ page }) => {
	await navigateToFirstPlan(page);

	const chip = page.getByTestId('strategy-plan-status');
	await expect(chip).toBeVisible({ timeout: 10_000 });
	/* Chip must have a non-empty recognisable status */
	const text = await chip.textContent();
	expect(['Draft', 'Active', 'Submitted', 'Approved', 'Archived']).toContain(
		text?.trim(),
	);
});

test('Workbench KPI cards hydrated with real data', async ({ page }) => {
	await navigateToFirstPlan(page);

	/* Overall Completion — not placeholder "—" */
	const compVal = page.locator('[data-swb="kpi-completion-val"]');
	await expect(compVal).toBeVisible({ timeout: 10_000 });
	await expect(compVal).not.toHaveText('—');

	/* Programs count — numeric */
	const progVal = page.locator('[data-swb="kpi-programs-val"]');
	await expect(progVal).toBeVisible();
	await expect(progVal).not.toHaveText('—');

	/* Indicators count */
	const indVal = page.locator('[data-swb="kpi-indicators-val"]');
	await expect(indVal).toBeVisible();
	await expect(indVal).not.toHaveText('—');
});

test('Back-to-hub link navigates to strategy-management', async ({ page }) => {
	await navigateToFirstPlan(page);

	const backLink = page.locator('[data-swb="back-link"]');
	await expect(backLink).toBeVisible({ timeout: 10_000 });
	await backLink.click();

	await expect(page).toHaveURL(/strategy-management/, { timeout: 15_000 });
});

test('Workbench shows sticky topbar with Strategic Alignment title', async ({ page }) => {
	await navigateToFirstPlan(page);

	const topbar = page.getByTestId('swb-topbar');
	await expect(topbar).toBeVisible({ timeout: 10_000 });
	await expect(topbar).toContainText('Strategic Alignment');
});
