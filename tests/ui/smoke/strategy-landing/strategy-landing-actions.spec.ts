import { test, expect } from '@playwright/test';

import { loginAsAdministrator, loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Manage Structure opens Structure tab in workspace', async ({ page }) => {
	test.skip(true, 'Requires per-plan workbench (selected-plan-open-builder) — pending workbench rewire');
	await loginAsAdministrator(page);
	await openStrategyLanding(page);

	await page.getByTestId('selected-plan-open-builder').click();

	await expect(page).toHaveURL(/strategy-management/);
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible({ timeout: 30_000 });
});

test('Edit Plan Info opens drawer', async ({ page }) => {
	test.skip(true, 'Requires per-plan workbench (selected-plan-edit-plan) — pending workbench rewire');
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await page.getByTestId('selected-plan-edit-plan').click();

	await expect(page.getByRole('heading', { name: /Edit Plan Info/i })).toBeVisible({ timeout: 15_000 });
	await expect(page).toHaveURL(/strategy-management/);
});

test('New Strategic Plan opens create drawer', async ({ page }) => {
	test.skip(true, 'Create button action requires backend wiring — pending');
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	/* Portfolio Hub: button is sph-create-plan-btn */
	await page.getByTestId('sph-create-plan-btn').click();

	await expect(page.getByRole('heading', { name: /New Strategic Plan/i })).toBeVisible({ timeout: 15_000 });
	await expect(page).toHaveURL(/strategy-management/);
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
	test.skip(true, 'Requires per-plan workbench tabs — pending workbench rewire');
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
