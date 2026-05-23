import { expect, test } from '@playwright/test';

import {
	loginAsPlanningAuthority,
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

test('Strategy Manager lands on Draft tab by default', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
	test.skip(!loggedIn, 'Strategy Manager test user not configured');
	await openBudgetLanding(page);

	await expect(page.getByTestId('budget-tab-draft')).toHaveClass(/is-active|kt-status-filter-active/);
});

test('Planning Authority lands on My Work tab by default', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
	test.skip(!loggedIn, 'Planning Authority test user not configured');
	await openBudgetLanding(page);

	await expect(page.getByTestId('budget-tab-my-work')).toHaveClass(/is-active|kt-status-filter-active/);
});

test('My Work tab filters to role-appropriate budgets', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
	test.skip(!loggedIn, 'Planning Authority test user not configured');
	await openBudgetLanding(page);

	await page.getByTestId('budget-tab-all').click();
	await expect(page.getByTestId('budget-tab-all')).toHaveClass(/is-active|kt-status-filter-active/);
	await expect(
		page
			.getByTestId('budget-list')
			.or(page.getByTestId('budget-tab-empty-state'))
			.or(page.getByTestId('budget-empty-state')),
	).toBeVisible({ timeout: 30_000 });
	const allCount = await page.locator('.kt-budget-row[data-budget]').count();
	test.skip(allCount === 0, 'No budgets on site for My Work filter smoke');

	await page.getByTestId('budget-tab-my-work').click();
	await expect(page.getByTestId('budget-tab-my-work')).toHaveClass(/is-active|kt-status-filter-active/, {
		timeout: 15_000,
	});
	const myCount = await page.locator('.kt-budget-row[data-budget]').count();
	expect(myCount).toBeLessThanOrEqual(allCount);

	if (myCount === 0) {
		await expect(page.getByTestId('budget-tab-empty-state')).toBeVisible();
		return;
	}

	const rows = page.locator('.kt-budget-row[data-budget]');
	const n = await rows.count();
	for (let i = 0; i < n; i++) {
		await expect(rows.nth(i).locator('[data-testid="budget-row-status-inline"]')).toContainText('Submitted');
	}
});
