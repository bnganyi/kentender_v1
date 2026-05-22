import { expect, type Page } from '@playwright/test';

/** Budget Management workspace Desk route (slug). */
export const BUDGET_LANDING_PATH = '/desk/budget-management';

export async function openBudgetLanding(page: Page) {
	await page.goto(BUDGET_LANDING_PATH, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('budget-landing-page')).toBeVisible({ timeout: 60_000 });
}

/** Open landing with all queue tabs visible (extended seed FY2026/FY2027). */
export async function openBudgetLandingAllQueues(page: Page) {
	await openBudgetLanding(page);
	const allTab = page.getByTestId('budget-tab-all');
	if ((await allTab.count()) > 0) {
		await allTab.click();
	}
}

export async function waitForFrappeBoot(page: Page) {
	await page.waitForFunction(() => {
		// @ts-ignore runtime frappe global
		return typeof window.frappe !== 'undefined' && !!window.frappe.boot;
	});
}
