import { expect, type Page } from '@playwright/test';

/** Strategy Management workspace Desk route (slug). */
export const STRATEGY_LANDING_PATH = '/desk/strategy-management';

export async function openStrategyLanding(page: Page) {
	await page.goto(STRATEGY_LANDING_PATH);
	await page.waitForLoadState('networkidle');
	await expect(page.getByTestId('strategy-landing-page')).toBeVisible({ timeout: 60_000 });
}
