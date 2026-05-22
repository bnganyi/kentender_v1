import { expect, type Locator, type Page } from '@playwright/test';

export async function expectListSelectionPreservesScroll(
	page: Page,
	list: Locator,
	rows: Locator,
	targetIndex: number,
) {
	const rowCount = await rows.count();
	expect(rowCount).toBeGreaterThan(targetIndex);

	await list.evaluate((el) => {
		el.scrollTop = el.scrollHeight;
	});
	const before = await list.evaluate((el) => el.scrollTop);
	await rows.nth(targetIndex).click({ force: true });
	const after = await list.evaluate((el) => el.scrollTop);

	expect(Math.abs(after - before)).toBeLessThanOrEqual(2);
}

export async function expectNoLoadingFlash(
	panel: Locator,
	loadingText: Locator,
	timeoutMs = 1500,
) {
	await expect(panel).toBeVisible({ timeout: 30000 });
	await expect(loadingText).toHaveCount(0, { timeout: timeoutMs });
}
