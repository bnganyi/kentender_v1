import { expect, Page } from '@playwright/test';

import { diaWorkspace } from './selectors';

/**
 * Open the DIA injected workbench shell (requires workspace route + JS inject).
 */
export async function openDIALanding(page: Page) {
	await page.goto(diaWorkspace.route, { waitUntil: 'domcontentloaded' });
	await page.waitForLoadState('domcontentloaded');
	await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });
}

export async function expectDiaShellVisible(page: Page) {
	await expect(page.getByTestId('dia-page-title')).toContainText(diaWorkspace.heading);
	await expect(page.getByTestId('dia-page-intro')).toContainText(diaWorkspace.introSnippet);
}
