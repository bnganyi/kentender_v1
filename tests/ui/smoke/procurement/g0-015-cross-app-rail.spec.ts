/**
 * G0-015 — Requisitioner: Strategy / Budget **workspace routes** keep the Procurement left rail
 * (`boot_session` / `_KT_WORKSPACE_TO_SIDEBAR` fast-path). Opens **Procurement Home** first via
 * **`/app/procurement-home`** (requires **Procurement Home** workspace **`module`: Desk** — see evidence).
 * Desk URLs use `/desk/strategy-management` and `/desk/budget-management` (same targets as spine links).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { procurementHomeWorkspace } from '../../helpers/procurement';
import { dismissOptionalDeskModals, workspaceAppPath } from '../../helpers/routes';

async function openRequisitionerProcurementHome(page: Page) {
	await page.goto(workspaceAppPath(procurementHomeWorkspace.heading));
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
	await expect(page.getByTestId('ph-landing-page')).toBeVisible({ timeout: 45_000 });
}

test.describe('G0-015 cross-app Procurement rail (Requisitioner)', () => {
	test('Strategy and Budget workspace routes keep Procurement sidebar rail', async ({ page }) => {
		test.setTimeout(90_000);
		await loginAsRequisitioner(page);
		// Prime Desk session from Procurement shell (matches real entry via G0-013 tile → home).
		await openRequisitionerProcurementHome(page);
		await dismissOptionalDeskModals(page);

		await page.goto('/desk/strategy-management');
		await page.waitForLoadState('domcontentloaded');
		await expect(page).toHaveURL(/strategy-management/i, { timeout: 45_000 });
		await expect(
			page.locator('.body-sidebar').getByRole('link', { name: 'Procurement Home', exact: true }).first(),
		).toBeVisible({ timeout: 45_000 });

		await openRequisitionerProcurementHome(page);
		await dismissOptionalDeskModals(page);
		await page.goto('/desk/budget-management');
		await page.waitForLoadState('domcontentloaded');
		await expect(page).toHaveURL(/budget-management/i, { timeout: 45_000 });
		await expect(
			page.locator('.body-sidebar').getByRole('link', { name: 'Procurement Home', exact: true }).first(),
		).toBeVisible({ timeout: 45_000 });
	});
});
