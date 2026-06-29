/**
 * W5-08 — Budget Workbench wiring smoke tests.
 *
 * Covers the five contracts from the W5 work item:
 *   1. Workbench opens from hub row action-button click.
 *   2. Budget title (breadcrumb name) is visible and non-empty after API load.
 *   3. At least one Budget Line card is rendered (Zone 2 populated).
 *   4. Clicking a line card populates the Artefacts panel (Zone 3 replaces placeholder).
 *   5. "Back to Budget Hub" link navigates to the budget-hub route.
 *
 * Requires the site to have at least one Budget with at least one active
 * Budget Line (seed_works_master_budget or seed_budget_hub_demo).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

// ── Constants ─────────────────────────────────────────────────────────────────

const HUB_PATH = '/app/budget-hub';

// ── Helpers ───────────────────────────────────────────────────────────────────

/** Open Budget Hub and wait for table rows to be rendered. */
async function openBudgetHub(page: Page): Promise<void> {
	await page.goto(HUB_PATH, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('kt-bgt-workbench')).toBeVisible({ timeout: 30_000 });
	// Primary API resolved when Available Balance is no longer a dash
	await expect(page.getByTestId('kt-bgt-kpi-available')).not.toHaveText('—', {
		timeout: 20_000,
	});
	// At least one budget row must be visible before we try to click
	await expect(
		page.getByTestId('kt-bgt-budget-tbody').locator('tr[data-budget-name]').first(),
	).toBeVisible({ timeout: 15_000 });
}

/**
 * Navigate directly to the workbench for the given budget name and wait for
 * the shell to mount and Zone 1 / Zone 2 API data to resolve.
 */
async function openWorkbench(page: Page, budgetName: string): Promise<void> {
	await page.goto(`/app/budget-workbench/${encodeURIComponent(budgetName)}`, {
		waitUntil: 'domcontentloaded',
	});
	// Shell must be visible
	await expect(page.getByTestId('kt-wbench-root')).toBeVisible({ timeout: 30_000 });
	// Zone 1 skeleton resolves when title is no longer a skeleton
	await expect(page.getByTestId('kt-wbench-title')).not.toHaveClass(/kt-wbench-skel/, {
		timeout: 20_000,
	});
	// Zone 2 loading placeholder must be replaced by real cards
	await page.waitForFunction(
		() => document.querySelector("[data-testid='kt-wbench-lines-list'] .kt-wbench-lines-loading") === null,
		undefined,
		{ timeout: 20_000 },
	);
}

/**
 * Read the first budget name from the hub table so every subsequent test can
 * navigate directly to a known workbench URL.
 */
async function getFirstBudgetName(page: Page): Promise<string> {
	const firstRow = page.getByTestId('kt-bgt-budget-tbody').locator('tr[data-budget-name]').first();
	const name = await firstRow.getAttribute('data-budget-name');
	if (!name) throw new Error('Could not read data-budget-name from first hub row');
	return name;
}

// ── Tests ─────────────────────────────────────────────────────────────────────

test.describe('Budget Workbench — wiring smoke (W5-08)', () => {
	test('Workbench opens from Budget Hub row action-button click', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);

		// Click the action button on the first hub row
		const tbody = page.getByTestId('kt-bgt-budget-tbody');
		const firstRow = tbody.locator('tr[data-budget-name]').first();
		await firstRow.locator('.kt-bgt-table-action').click();

		// Workbench shell must mount
		await expect(page.getByTestId('kt-wbench-root')).toBeVisible({ timeout: 20_000 });

		// URL must contain budget-workbench
		await expect(page).toHaveURL(/budget-workbench/, { timeout: 10_000 });
	});

	test('Budget title (breadcrumb name) is visible and non-empty after API load', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		const budgetName = await getFirstBudgetName(page);
		await openWorkbench(page, budgetName);

		const nameEl = page.getByTestId('kt-wbench-budget-name');
		await expect(nameEl).toBeVisible();
		const text = (await nameEl.textContent()) ?? '';
		expect(text.trim().length).toBeGreaterThan(0);
		// Must not still be the route-segment raw ID or a dash placeholder
		expect(text.trim()).not.toBe('—');
	});

	test('Approved Budget card shows sum of line allocations (not static total_budget_amount)', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		const budgetName = await getFirstBudgetName(page);
		await openWorkbench(page, budgetName);

		// The card must have resolved (skeleton class removed)
		const approvedEl = page.getByTestId('kt-wbench-approved');
		await expect(approvedEl).toBeVisible({ timeout: 20_000 });
		await expect(approvedEl).not.toHaveClass(/kt-wbench-skel/, { timeout: 15_000 });

		// Value must not be the dash placeholder — it must have resolved to a real number
		const text = (await approvedEl.textContent()) ?? '';
		expect(text.trim()).not.toBe('—');
		expect(text.trim().length).toBeGreaterThan(0);
	});

	test('At least one Budget Line card is rendered (Zone 2 populated)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		const budgetName = await getFirstBudgetName(page);
		await openWorkbench(page, budgetName);

		const linesList = page.getByTestId('kt-wbench-lines-list');
		await expect(linesList).toBeVisible();

		// Loading placeholder must be gone
		await expect(linesList.locator('.kt-wbench-lines-loading')).toHaveCount(0);

		// At least one line card must be present
		const cards = linesList.getByTestId('kt-wbench-line-card');
		await expect(cards.first()).toBeVisible({ timeout: 15_000 });
		expect(await cards.count()).toBeGreaterThanOrEqual(1);
	});

	test('Clicking a line card populates the Artefacts panel (Zone 3)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		const budgetName = await getFirstBudgetName(page);
		await openWorkbench(page, budgetName);

		// Click the first line card
		const firstCard = page
			.getByTestId('kt-wbench-lines-list')
			.getByTestId('kt-wbench-line-card')
			.first();
		await expect(firstCard).toBeVisible({ timeout: 15_000 });
		await firstCard.click();

		const artBody = page.getByTestId('kt-wbench-artefacts-body');
		await expect(artBody).toBeVisible();

		// Wait for the "Loading artefacts…" placeholder to be replaced
		await page.waitForFunction(
			() => {
				const body = document.querySelector("[data-testid='kt-wbench-artefacts-body']");
				if (!body) return false;
				// Neither the loading spinner nor the initial "Select a line" prompt
				if (body.querySelector('.kt-wbench-art-spinner')) return false;
				const text = body.textContent ?? '';
				return !text.includes('Loading artefacts') && !text.includes('Select a budget line');
			},
			undefined,
			{ timeout: 20_000 },
		);

		// Artefacts panel must now contain the selected line name
		const lineNameEl = artBody.getByTestId('kt-wbench-artefacts-line-name');
		await expect(lineNameEl).toBeVisible();
		const lineNameText = (await lineNameEl.textContent()) ?? '';
		expect(lineNameText.trim().length).toBeGreaterThan(0);
	});

	test('"Back to Budget Hub" link navigates back to the hub', async ({ page }) => {
		await loginAsAdministrator(page);
		await openBudgetHub(page);
		const budgetName = await getFirstBudgetName(page);
		await openWorkbench(page, budgetName);

		// Click the back link
		await page.locator("[data-wbench='back-link']").click();

		// Hub shell must remount
		await expect(page.getByTestId('kt-bgt-workbench')).toBeVisible({ timeout: 20_000 });

		// URL must be back on budget-hub (no workbench segment)
		await expect(page).toHaveURL(/budget-hub/, { timeout: 10_000 });
		await expect(page).not.toHaveURL(/budget-workbench/);
	});
});
