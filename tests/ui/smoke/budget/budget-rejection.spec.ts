/**
 * B5.15 — Budget rejection flow (8.a.Budget-Approval-Flow - 2.md).
 * Credential-aware; requires Planning Authority + Strategy Manager users in `.env.ui` when exercising role paths.
 */

import { expect, test, type Page } from '@playwright/test';

import {
	loginAsAdministrator,
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

async function selectBudgetRowByTitle(page: Page, title: string) {
	const row = page.locator('.kt-budget-row').filter({ hasText: title }).first();
	await expect(row).toBeVisible({ timeout: 30_000 });
	await row.click();
	await expect(row).toHaveClass(/is-active/);
}

test('Budget landing exposes Rejected tab and reject modal test ids (Administrator)', async ({ page }) => {
	await loginAsAdministrator(page);
	await openBudgetLanding(page);

	await expect(page.getByTestId('budget-tab-rejected')).toBeVisible();
	await page.getByTestId('budget-tab-rejected').click();
	await expect(page.getByTestId('budget-tab-rejected')).toHaveClass(/btn-primary/);
});

test('Planning Authority can open reject dialog on Submitted budget (seeded FY2027)', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
	test.skip(!loggedIn, 'Planning Authority test user not configured');
	await openBudgetLanding(page);

	const row2027 = page.locator('.kt-budget-row').filter({ hasText: 'FY2027 Budget' });
	const hasRow = await row2027.count();
	test.skip(hasRow === 0, 'Requires seed_budget_extended (FY2027 budget)');

	await selectBudgetRowByTitle(page, 'FY2027 Budget');
	const badge = page.getByTestId('selected-budget-status-badge');
	const st = await badge.textContent();
	if (st?.includes('Approved')) {
		test.skip(true, 'FY2027 already Approved — need Submitted budget to test reject UI');
		return;
	}
	if (!st?.includes('Submitted')) {
		test.skip(true, 'FY2027 not Submitted — cannot test reject button');
		return;
	}

	await page.getByTestId('budget-reject').click();
	await expect(page.getByTestId('budget-reject-modal')).toBeVisible({ timeout: 15_000 });
	await expect(page.getByTestId('budget-reject-reason-input')).toBeVisible();
	await page.getByRole('button', { name: 'Cancel', exact: true }).click();
});

test('Strategy Manager sees rejection summary when a Rejected budget is selected', async ({ page }) => {
	const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
	test.skip(!loggedIn, 'Strategy Manager test user not configured');
	await openBudgetLanding(page);
	await page.getByTestId('budget-tab-rejected').click();
	const n = await page.locator('.kt-budget-row').count();
	test.skip(n === 0, 'No Rejected budgets in site — reject a Submitted budget first');
	await page.locator('.kt-budget-row').first().click();
	await expect(page.getByTestId('budget-rejection-summary')).toBeVisible({ timeout: 15_000 });
});
