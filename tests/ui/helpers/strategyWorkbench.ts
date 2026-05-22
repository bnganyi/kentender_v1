import { Page, expect } from '@playwright/test';

import { openStrategyLanding } from './strategyLanding';

export async function selectStrategicPlan(page: Page, planName: string) {
	const row = page.getByTestId(`strategic-plan-row-${planName}`);
	await expect(row).toBeVisible({ timeout: 30_000 });
	await row.click();
	await expect(page.getByTestId('selected-plan-panel')).toBeVisible({ timeout: 15_000 });
}

export async function openStrategyStructureTab(page: Page, planName?: string) {
	await openStrategyLanding(page);
	if (planName) {
		await selectStrategicPlan(page, planName);
	}
	await page.getByTestId('strategy-tab-structure').click();
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible({ timeout: 30_000 });
}

export async function openStrategyReviewTab(page: Page, planName?: string) {
	await openStrategyLanding(page);
	if (planName) {
		await selectStrategicPlan(page, planName);
	}
	await page.getByTestId('strategy-tab-review').click();
	await expect(page.getByTestId('strategy-review-panel')).toBeVisible({ timeout: 30_000 });
}

export async function switchPlanTab(page: Page, testId: string) {
	await page.getByTestId(testId).click();
}

export async function clickStructureSubtab(page: Page, subtabTestId: string, readyTestId: string) {
	await page.getByTestId(subtabTestId).click();
	await expect(page.getByTestId(readyTestId)).toBeVisible({ timeout: 15_000 });
}

/** Fill and save a Frappe ui.Dialog primary action. */
export async function saveVisibleDialog(page: Page) {
	const d = page.locator('.modal.show').last();
	await expect(d).toBeVisible();
	await Promise.all([
		page.waitForResponse((r) => r.request().method() === 'POST' && r.ok(), { timeout: 60_000 }),
		d.locator('.modal-footer button.btn-primary').click(),
	]);
	await expect(d).toBeHidden({ timeout: 30_000 });
}
