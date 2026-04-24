import { expect, type Page } from '@playwright/test';

/** Budget Management workspace Desk route (slug). */
export const BUDGET_LANDING_PATH = '/desk/budget-management';

export async function openBudgetLanding(page: Page) {
	await page.goto(BUDGET_LANDING_PATH);
	await page.waitForLoadState('networkidle');
	await expect(page.getByTestId('budget-landing-page')).toBeVisible({ timeout: 60_000 });
}

/** Activates the All tab so Submitted / Approved budgets appear (role defaults often hide them). */
export async function openBudgetLandingAllQueues(page: Page) {
	await openBudgetLanding(page);
	await page.getByTestId('budget-tab-all').click();
	await expect(page.getByTestId('budget-tab-all')).toHaveClass(/btn-primary/);
}
