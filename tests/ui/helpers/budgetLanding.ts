import { expect, test, type Page } from '@playwright/test';

/** Budget Management workspace Desk route (slug). */
export const BUDGET_LANDING_PATH = '/desk/budget-management';

/** Wait until Frappe `frappe.session` is present (avoids `frappe.call` 417 in `page.evaluate`). */
export async function waitForFrappeBoot(page: Page) {
	await page.waitForFunction(
		() => {
			const f = (window as { frappe?: { session?: { user?: string } } }).frappe;
			return Boolean(f && f.session && f.session.user);
		},
		{ timeout: 60_000 },
	);
}

export type OpenBudgetLandingOptions = {
	/**
	 * When true, skip the test if Desk shows "Not permitted" for this user (e.g. role missing
	 * Page/Workspace access on a partially seeded site). Administrator flows omit this.
	 */
	skipIfNotPermitted?: boolean;
};

export async function openBudgetLanding(page: Page, opts?: OpenBudgetLandingOptions) {
	await page.goto(BUDGET_LANDING_PATH, { waitUntil: 'domcontentloaded' });
	await waitForFrappeBoot(page);
	await page.waitForLoadState('networkidle').catch(() => {});
	const denied = await page
		.getByRole('heading', { name: 'Not permitted' })
		.isVisible({ timeout: 5000 })
		.catch(() => false);
	test.skip(
		Boolean(opts?.skipIfNotPermitted && denied),
		'User lacks permission for Budget Management desk route on this site.',
	);
	await expect(page.getByTestId('budget-landing-page')).toBeVisible({ timeout: 60_000 });
}

/** Activates the All tab so Submitted / Approved budgets appear (role defaults often hide them). */
export async function openBudgetLandingAllQueues(page: Page, opts?: OpenBudgetLandingOptions) {
	await openBudgetLanding(page, opts);
	await page.getByTestId('budget-tab-all').click();
	await expect(page.getByTestId('budget-tab-all')).toHaveClass(/btn-primary/);
}
