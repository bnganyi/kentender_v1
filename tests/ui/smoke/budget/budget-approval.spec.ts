/**
 * B5.7 — Budget approval flow (8.Budget-Approval-Flow.md).
 */

import { expect, test, type Page } from '@playwright/test';

import {
	loginAsAdministrator,
	loginAsPlanningAuthority,
	loginAsStrategyManager,
} from '../../helpers/auth';
import { openBudgetLanding, openBudgetLandingAllQueues } from '../../helpers/budgetLanding';

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

async function confirmFrappeYes(page: Page) {
	const yes = page.getByRole('button', { name: 'Yes', exact: true });
	await expect(yes).toBeVisible({ timeout: 15_000 });
	await yes.click();
}

async function selectBudgetRowByTitle(page: Page, title: string) {
	const row = page.locator('.kt-budget-row').filter({ hasText: title }).first();
	await expect(row).toBeVisible({ timeout: 30_000 });
	await row.click();
	await expect(row).toHaveClass(/is-active/);
}

async function openReviewTab(page: Page) {
	await page.getByTestId('budget-tab-review').click();
	await expect(page.getByTestId('budget-review-panel')).toBeVisible({ timeout: 30_000 });
}

test.describe.serial('Budget approval flow (B5.7)', () => {
	let seedOk = false;

	test.beforeAll(async ({ browser }) => {
		const page = await browser.newPage();
		try {
			await loginAsAdministrator(page);
			await openBudgetLanding(page);
			const n2026 = await page.locator('.kt-budget-row').filter({ hasText: 'FY2026 Budget' }).count();
			const n2027 = await page.locator('.kt-budget-row').filter({ hasText: 'FY2027 Budget' }).count();
			seedOk = n2026 > 0 && n2027 > 0;
		} finally {
			await page.close();
		}
	});

	test.beforeEach(async () => {
		test.skip(
			!seedOk,
			'Requires seed_budget_extended (FY2026 + FY2027 budgets). Run: bench execute kentender_core.seeds.seed_budget_extended.run',
		);
	});

	test('FY2027 allocations are read-only when budget is Submitted', async ({ page }) => {
		const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
		test.skip(!loggedIn, 'Strategy Manager test user not configured');
		await openBudgetLandingAllQueues(page);
		await selectBudgetRowByTitle(page, 'FY2027 Budget');
		const badge = page.getByTestId('selected-budget-status-badge');
		const st = await badge.textContent();
		if (st?.includes('Approved')) {
			test.skip(true, 'FY2027 already Approved — re-run seed_budget_extended for Submitted FY2027');
			return;
		}
		if (!st?.includes('Submitted')) {
			test.skip(true, `FY2027 not Submitted — re-run seed_budget_extended`);
			return;
		}
		await page.getByTestId('budget-tab-allocations').click();
		await expect(page.getByTestId('budget-allocations-readonly-banner')).toBeVisible();
		await expect(page.getByTestId('budget-allocation-add')).toHaveCount(0);
	});

	test('Strategy Manager does not see Approve on Submitted budget (FY2027)', async ({ page }) => {
		const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
		test.skip(!loggedIn, 'Strategy Manager test user not configured');
		await openBudgetLandingAllQueues(page);
		await selectBudgetRowByTitle(page, 'FY2027 Budget');
		const badge = page.getByTestId('selected-budget-status-badge');
		const st = await badge.textContent();
		if (st?.includes('Approved') || !st?.includes('Submitted')) {
			test.skip(true, 'FY2027 not in Submitted state for this assertion');
			return;
		}
		await openReviewTab(page);
		await expect(page.getByTestId('budget-approve')).toHaveCount(0);
		await expect(page.getByTestId('selected-budget-edit')).toHaveCount(0);
		await expect(badge).toContainText('Submitted');
	});

	test('Strategy Manager can submit Draft budget (FY2026)', async ({ page }) => {
		const loggedIn = await tryLogin(() => loginAsStrategyManager(page));
		test.skip(!loggedIn, 'Strategy Manager test user not configured');
		await openBudgetLandingAllQueues(page);
		await selectBudgetRowByTitle(page, 'FY2026 Budget');
		await openReviewTab(page);

		const submit = page.getByTestId('budget-submit-approval');
		const statusBadge = page.getByTestId('selected-budget-status-badge');
		if ((await submit.count()) === 0) {
			const t = (await statusBadge.textContent()) || '';
			if (t.includes('Submitted')) {
				test.skip(true, 'FY2026 already Submitted');
				return;
			}
			test.skip(true, 'FY2026 Submit hidden — check seed preconditions');
			return;
		}

		await submit.click();
		await confirmFrappeYes(page);
		await expect(statusBadge).toContainText('Submitted', { timeout: 30_000 });
	});

	test('Planning Authority can approve Submitted budget (FY2027)', async ({ page }) => {
		const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
		test.skip(!loggedIn, 'Planning Authority test user not configured');
		await openBudgetLandingAllQueues(page);
		await selectBudgetRowByTitle(page, 'FY2027 Budget');
		await openReviewTab(page);

		const approve = page.getByTestId('budget-approve');
		if ((await approve.count()) === 0) {
			await expect(page.getByTestId('selected-budget-status-badge')).toContainText('Approved');
			test.skip(true, 'FY2027 already Approved');
			return;
		}

		await approve.click();
		await confirmFrappeYes(page);
		await expect(page.getByTestId('selected-budget-status-badge')).toContainText('Approved', {
			timeout: 30_000,
		});
	});

	test('FY2027 allocations are read-only when budget is Approved', async ({ page }) => {
		const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
		test.skip(!loggedIn, 'Planning Authority test user not configured');
		await openBudgetLandingAllQueues(page);
		await selectBudgetRowByTitle(page, 'FY2027 Budget');
		await expect(page.getByTestId('selected-budget-status-badge')).toContainText('Approved');
		await page.getByTestId('budget-tab-allocations').click();
		await expect(page.getByTestId('budget-allocations-readonly-banner')).toContainText('approved and locked');
		await expect(page.getByTestId('budget-allocation-add')).toHaveCount(0);
	});

	test('Planning Authority does not see Submit or Edit on Approved FY2027', async ({ page }) => {
		const loggedIn = await tryLogin(() => loginAsPlanningAuthority(page));
		test.skip(!loggedIn, 'Planning Authority test user not configured');
		await openBudgetLandingAllQueues(page);
		await selectBudgetRowByTitle(page, 'FY2027 Budget');
		await openReviewTab(page);
		await expect(page.getByTestId('budget-submit-approval')).toHaveCount(0);
		await expect(page.getByTestId('selected-budget-edit')).toHaveCount(0);
	});
});
