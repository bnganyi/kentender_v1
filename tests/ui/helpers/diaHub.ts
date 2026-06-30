/**
 * DIA Hub page helper utilities.
 *
 * Used by smoke tests for the demand-hub Frappe custom page (H14).
 */
import { expect, type Page } from '@playwright/test';

export const DIA_HUB_PATH = '/app/demand-hub';

/**
 * Navigate to the Demand Hub and wait until:
 *   1. The hub root element is visible.
 *   2. Initial skeleton rows have been replaced (first API call completed).
 *
 * If no demand records are seeded the table will show an empty-state row —
 * `hasRows` will be false but the page is still considered "ready".
 */
export async function openDemandHub(page: Page): Promise<{ hasRows: boolean }> {
	await page.goto(DIA_HUB_PATH, { waitUntil: 'domcontentloaded' });

	// Hub root must mount
	await expect(page.getByTestId('kt-dia-hub')).toBeVisible({ timeout: 30_000 });

	// First load shows skeleton rows; wait for them to be replaced
	await page.waitForFunction(
		() => document.querySelectorAll('.kt-dia-skeleton-row').length === 0,
		undefined,
		{ timeout: 25_000 },
	);

	const rowCount = await page
		.getByTestId('kt-dia-table-body')
		.locator('tr[data-demand-name]')
		.count();

	return { hasRows: rowCount > 0 };
}

/**
 * Wait for a table reload triggered by a chip/search/filter action.
 *
 * After the first load, subsequent reloads no longer replace rows with
 * skeleton — they add `.kt-dia-table-body--loading` (dim) then remove it.
 * We wait for both the dim class to clear AND the tbody to no longer contain
 * skeleton rows (covers the first-load edge case if called then too).
 */
export async function waitForTableReload(page: Page): Promise<void> {
	await page.waitForFunction(
		() => {
			const tbody = document.querySelector('[data-testid="kt-dia-table-body"]');
			if (!tbody) return false;
			if (tbody.classList.contains('kt-dia-table-body--loading')) return false;
			if (tbody.querySelectorAll('.kt-dia-skeleton-row').length > 0) return false;
			return true;
		},
		undefined,
		{ timeout: 20_000 },
	);
}

/** Return the `data-demand-name` attribute of the first visible demand row, or null. */
export async function getFirstDemandName(page: Page): Promise<string | null> {
	const row = page
		.getByTestId('kt-dia-table-body')
		.locator('tr[data-demand-name]')
		.first();
	if (!(await row.isVisible().catch(() => false))) return null;
	return row.getAttribute('data-demand-name');
}
