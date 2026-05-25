import { expect, Page } from '@playwright/test';

import { dismissOptionalDeskModals } from './routes';
import { diaWorkspace } from './selectors';

/**
 * Open DIA the same way as Desk: `frappe.set_route("Workspaces", "Demand Intake and Approval")`.
 * Deep-linking to `/app/demand-intake-and-approval` or `/desk/...` can resolve to a missing legacy
 * `Page` document instead of the Workspace in current Frappe.
 */
export async function navigateToDiaWorkspace(page: Page) {
	await page.goto('/app', { waitUntil: 'domcontentloaded' });
	await page.waitForLoadState('domcontentloaded');
	await page.waitForFunction(
		() => typeof (window as { frappe?: { set_route?: (a: string, b: string) => void } }).frappe
			?.set_route === 'function',
		{ timeout: 60_000 },
	);
	await page.evaluate((title: string) => {
		(
			window as { frappe: { set_route: (a: string, b: string) => void } }
		).frappe.set_route('Workspaces', title);
	}, diaWorkspace.heading);
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
}

/**
 * Open the DIA injected workbench shell (requires workspace route + JS inject).
 */
export async function openDIALanding(page: Page) {
	await navigateToDiaWorkspace(page);
	const landing = page.getByTestId('dia-landing-page');
	await landing.waitFor({ state: 'attached', timeout: 60_000 });
	const initiallyVisible = await landing.isVisible().catch(() => false);
	if (!initiallyVisible) {
		// Desk route transitions can briefly leave an attached-but-hidden shell. Re-route once, then assert visible.
		await page.evaluate((title: string) => {
			(
				window as { frappe: { set_route: (a: string, b: string) => void } }
			).frappe.set_route('Workspaces', title);
		}, diaWorkspace.heading);
	}
	await expect(landing).toBeVisible({ timeout: 60_000 });
}

export async function expectDiaShellVisible(page: Page) {
	await expect(page.getByTestId('dia-page-title')).toContainText('Demand');
	await expect(page.getByTestId('dia-page-intro')).toContainText('procurement');
}

/** Open Review tab where workflow actions live (Phase 0–2). */
export async function openDiaReviewTab(page: Page) {
	await page.getByTestId('dia-tab-review').click();
	await expect(page.getByTestId('dia-review-panel')).toBeVisible({ timeout: 20_000 });
}
