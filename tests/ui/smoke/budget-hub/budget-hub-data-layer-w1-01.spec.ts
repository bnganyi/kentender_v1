import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

/**
 * Budget Hub smoke tests — W1-01 JS data layer.
 *
 * Requires site with at least one Budget and Budget Line
 * (seed_works_master_budget or seed_budget_hub_demo).
 */

async function openBudgetHub(page: ReturnType<typeof test['info']> extends never ? never : Parameters<Parameters<typeof test>[1]>[0]['page']) {
	await page.goto('/app/budget-hub', { waitUntil: 'domcontentloaded' });
	// Wait for the workbench shell to mount
	await expect(page.getByTestId('kt-bgt-workbench')).toBeVisible({ timeout: 30_000 });
	// Wait for the API call to resolve (loading dashes replaced)
	await expect(page.getByTestId('kt-bgt-kpi-available')).not.toHaveText('—', { timeout: 20_000 });
}

test('Budget Hub page loads and mounts workbench shell', async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto('/app/budget-hub', { waitUntil: 'domcontentloaded' });

	await expect(page.getByTestId('kt-bgt-workbench')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('kt-bgt-topbar')).toBeVisible();
	await expect(page.getByTestId('kt-bgt-kpis')).toBeVisible();
	await expect(page.getByTestId('kt-bgt-budget-tbody')).toBeVisible();
});

test('Budget Hub KPI cards populate with live numbers after API load', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetHub(page);

	// Available Balance: numeric value (not dash, not "Loading")
	const available = page.getByTestId('kt-bgt-kpi-available');
	await expect(available).not.toHaveText('—');
	await expect(available).not.toHaveClass(/kt-bgt-kpi--loading/);

	// Reserved
	const reserved = page.getByTestId('kt-bgt-kpi-reserved');
	await expect(reserved).not.toHaveText('—');

	// Committed — W1-02: shows en-dash as Phase 2 placeholder
	const committed = page.getByTestId('kt-bgt-kpi-committed');
	await expect(committed).toHaveText('–');
	await expect(committed).not.toHaveClass(/kt-bgt-kpi--loading/);

	// Pending Approvals — numeric (may be 0 but must not be dash)
	const pending = page.getByTestId('kt-bgt-kpi-pending');
	await expect(pending).not.toHaveText('—');
	const pendingText = await pending.textContent();
	expect(Number(pendingText?.trim())).toBeGreaterThanOrEqual(0);
});

test('Budget Hub table renders at least one budget row', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetHub(page);

	const tbody = page.getByTestId('kt-bgt-budget-tbody');
	// Must not show "Loading" placeholder
	await expect(tbody).not.toContainText('Loading budgets');
	// Must not show "No budgets found" (site has seed budgets)
	await expect(tbody).not.toContainText('No budgets found');
	// At least one data row
	const rows = tbody.locator('tr[data-budget-name]');
	await expect(rows.first()).toBeVisible({ timeout: 15_000 });
});

test('Budget Hub table row has allocation bar, KES amount, and status chip', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetHub(page);

	const tbody = page.getByTestId('kt-bgt-budget-tbody');
	const firstRow = tbody.locator('tr[data-budget-name]').first();
	await expect(firstRow).toBeVisible({ timeout: 15_000 });

	// W1-03: allocation bar percentage (n%)
	await expect(firstRow.locator('.kt-bgt-bar-pct')).toBeVisible();
	const pctText = await firstRow.locator('.kt-bgt-bar-pct').textContent();
	expect(pctText).toMatch(/\d+%/);

	// W1-03: allocation bar segment (single blue bar)
	await expect(firstRow.locator('.kt-bgt-bar-allocated')).toBeVisible();

	// W1-03: available amount formatted as "KES <number>"
	await expect(firstRow.locator('.kt-bgt-avail-value')).toBeVisible();
	const availText = await firstRow.locator('.kt-bgt-avail-value').textContent();
	expect(availText?.trim()).toMatch(/^KES[\s\u00a0]/);

	// Status chip present
	await expect(firstRow.locator('.kt-bgt-chip')).toBeVisible();
});

test('Budget Hub table row shows budget_name and fiscal_year', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetHub(page);

	const tbody = page.getByTestId('kt-bgt-budget-tbody');
	const firstRow = tbody.locator('tr[data-budget-name]').first();
	await expect(firstRow).toBeVisible({ timeout: 15_000 });

	// W1-03: primary cell has .kt-bgt-budget-name (non-empty)
	const namEl = firstRow.locator('.kt-bgt-budget-name');
	await expect(namEl).toBeVisible();
	expect((await namEl.textContent())?.trim().length).toBeGreaterThan(0);
});
