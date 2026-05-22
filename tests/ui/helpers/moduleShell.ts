import { expect, Page } from '@playwright/test';

/** Assert the shared KenTender module shell exposes a back-to-workbench control. */
export async function expectBackToWorkbench(page: Page) {
	const back = page.getByTestId('back-to-workbench');
	await expect(back).toBeVisible({ timeout: 30_000 });
	await expect(back).toBeEnabled();
}

/** Click back-to-workbench and wait for workspace route navigation. */
export async function clickBackToWorkbench(page: Page) {
	await expectBackToWorkbench(page);
	await page.getByTestId('back-to-workbench').click();
}
