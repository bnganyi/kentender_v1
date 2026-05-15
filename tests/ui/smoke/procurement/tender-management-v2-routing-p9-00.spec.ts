/**
 * P9-00 / R03 — Tender Management v2 workbench route (doc 9 §14.1, doc 6 §3).
 * Route: `/app/tender-management-v2` and `/desk/tender-management-v2`; first paint includes `tm2-workbench-page`.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals, openWorkspaceFromDeskLauncher } from '../../helpers/routes';
import { procurementModule } from '../../helpers/selectors';

test.describe('Tender Management v2 routing (P9-00 / R03)', () => {
	test.setTimeout(180_000);

	test('app/tender-management-v2 shows workbench shell (not TM2 list redirect)', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('tm2-workbench-page')).toBeVisible({ timeout: 90_000 });
		await expect(page.getByTestId('tm2-page-title')).toHaveText('Tender Management');
		await expect(page).toHaveURL(/tender-management-v2/i, { timeout: 90_000 });
		await expect(page).not.toHaveURL(/List\/TM2%20Tender|List\/TM2 Tender/i);
	});

	test('desk/tender-management-v2 shows workbench shell', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/desk/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('tm2-workbench-page')).toBeVisible({ timeout: 90_000 });
	});

	test('Procurement sidebar Tender Management opens workbench', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Tender Management');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('tm2-workbench-page')).toBeVisible({ timeout: 90_000 });
		await expect(page).toHaveURL(/tender-management-v2/i, { timeout: 90_000 });
	});
});
