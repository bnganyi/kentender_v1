import { expect, test } from '@playwright/test';

import {
	loginAsPlanningAuthority,
	loginAsRequisitioner,
	loginAsStrategyManager,
} from '../../helpers/auth';
import { openBudgetLanding } from '../../helpers/budgetLanding';

async function tryLogin(fn: () => Promise<void>) {
	try {
		await fn();
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('Invalid Login')) {
			return false;
		}
		throw e;
	}
}

test('Strategy Manager has create, work tabs, and allocations on landing', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
	test.skip(!loggedIn, 'Strategy Manager test user not configured in this environment');
	await openBudgetLanding(page);

	await expect(page.getByTestId('budget-create-button')).toBeVisible();
	await expect(page.getByTestId('budget-tab-draft')).toBeVisible();
	await page.getByTestId('budget-tab-all').click();
	const firstRow = page.locator('.kt-budget-row[data-budget]').first();
	await expect(firstRow).toBeVisible({ timeout: 30_000 });
	await firstRow.click();
	await page.getByTestId('budget-tab-allocations').click();
	await expect(page.getByTestId('budget-allocations-table')).toBeVisible({ timeout: 30_000 });
	const status = await page.getByTestId('selected-budget-status-badge').textContent();
	if (status?.includes('Draft') || status?.includes('Rejected')) {
		await expect(page.getByTestId('budget-allocation-add')).toBeVisible();
	}
});

test('Planning Authority has read-only Budget landing access', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
	test.skip(!loggedIn, 'Planning Authority test user not configured in this environment');
	await openBudgetLanding(page);

	await expect(
		page
			.getByTestId('budget-list')
			.or(page.getByTestId('budget-empty-state'))
			.or(page.getByTestId('budget-tab-empty-state')),
	).toBeVisible();
	await expect(page.getByTestId('budget-create-button')).toHaveCount(0);
	await expect(page.getByTestId('budget-tab-my-work')).toBeVisible();
});

test('Requisitioner cannot access Budget landing workspace', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsRequisitioner(page));
	test.skip(!loggedIn, 'Requisitioner test user not configured in this environment');
	await page.goto('/desk/budget-management', { waitUntil: 'domcontentloaded' });

	await expect(page.getByTestId('budget-landing-page')).toHaveCount(0);
});
