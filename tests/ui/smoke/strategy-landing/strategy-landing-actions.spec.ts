import { test, expect } from '@playwright/test';

import { loginAsAdministrator, loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Plan card CTA navigates to strategy workbench for the selected plan', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	/* Wait for a real plan card to appear */
	const firstCard = page.getByTestId('sph-plan-card').first();
	await expect(firstCard).toBeVisible({ timeout: 15_000 });

	/* Click the CTA button (View Workbench / Continue Setup) */
	const cta = firstCard.getByTestId('sph-plan-cta');
	await expect(cta).toBeVisible();
	const planName = await firstCard.getAttribute('data-plan-name');

	await cta.click();

	/* Should navigate to the strategy-builder page */
	await expect(page).toHaveURL(/strategy-builder/, { timeout: 15_000 });

	/* The strategy builder shell must render — not a blank page */
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 20_000 });

	/* The route should contain the plan name */
	if (planName) {
		const decoded = decodeURIComponent(planName);
		await expect(page).toHaveURL(new RegExp(encodeURIComponent(decoded).replace(/[.*+?^${}()|[\]\\]/g, '\\$&')), { timeout: 5_000 });
	}
});

test('Clicking anywhere on a plan card body navigates to strategy workbench', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const firstCard = page.getByTestId('sph-plan-card').first();
	await expect(firstCard).toBeVisible({ timeout: 15_000 });

	/* Click the card title (not the ⋮ button) */
	const cardTitle = firstCard.locator('.kt-sph-card-title').first();
	await cardTitle.click();

	await expect(page).toHaveURL(/strategy-builder/, { timeout: 15_000 });
	/* Builder shell renders — not blank */
	await expect(page.getByTestId('strategy-builder-page')).toBeVisible({ timeout: 20_000 });
});

test('New Strategic Plan opens create form', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('sph-create-plan-btn').click();

	/* frappe.new_doc navigates to the Strategic Plan form URL — Frappe slugifies the doctype name */
	await expect(page).toHaveURL(/strategic-plan\/new-strategic-plan/, { timeout: 15_000 });
});

test('Search keeps focus while typing', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	/* Portfolio Hub: search is in the topbar */
	const search = page.getByTestId('sph-search-input');
	await search.click();
	await search.type('u');
	await expect(search).toBeFocused();
	await search.type('p');
	await expect(search).toBeFocused();
	await expect(search).toHaveValue('up');
});

test('Detail tab switch preserves list scroll position', async ({ page }) => {
	test.skip(true, 'Requires per-plan workbench tabs — future workbench wiring');
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	const list = page.getByTestId('strategic-plan-list');
	await expect(list).toBeVisible();
	await list.evaluate((el) => {
		el.scrollTop = el.scrollHeight;
	});

	const before = await list.evaluate((el) => el.scrollTop);
	await expect(before).toBeGreaterThan(0);

	await page.getByTestId('strategy-tab-review').click();
	await expect(page.getByTestId('strategy-tab-panel-review')).toBeVisible();

	const after = await page.getByTestId('strategic-plan-list').evaluate((el) => el.scrollTop);
	expect(Math.abs(after - before)).toBeLessThanOrEqual(2);
});
