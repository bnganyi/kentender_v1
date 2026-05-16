/**
 * R5-005 / LV-R5-005-01 — Planning workbench package list/detail show linked Procurement Journey.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';
import {
	openProcurementWorkspaceFromModule,
	procurementPlanningWorkspace,
} from '../../helpers/procurement';

const PKG_CODE = 'PKG-MOH-2026-001';
const PKG_ROW_SLUG = 'pkg-moh-2026-001';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('Procurement Planning package journey linkage (R5-005)', () => {
	test('PLC-R5-005-01: WORKS package row and detail expose journey link', async ({ page }) => {
		await loginAsAdministrator(page);

		const hasPkg = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Procurement Package',
						filters: [['package_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
					error: reject,
				});
			});
		}, PKG_CODE);
		test.skip(!hasPkg, 'WORKS Procurement Package PKG-MOH-2026-001 not on site.');

		await page.goto('/app', { waitUntil: 'domcontentloaded' });
		await dismissOptionalDeskModals(page);
		await openProcurementWorkspaceFromModule(page, procurementPlanningWorkspace.heading);

		await expect(page.getByTestId('pp-page-title')).toContainText('Procurement Planning', {
			timeout: 90_000,
		});

		await page.getByTestId('pp-tab-all').click({ timeout: 30_000 });
		await page.getByTestId('pp-queue-all-packages').click({ timeout: 45_000 });

		await page.getByTestId('pp-package-search').fill(PKG_CODE);

		const row = page.getByTestId(`pp-row-${PKG_ROW_SLUG}`);
		await expect(row).toBeVisible({ timeout: 60_000 });

		const rowJourneyLink = page.getByTestId(`pp-row-journey-link-${PKG_ROW_SLUG}`);
		await expect(rowJourneyLink).toBeVisible({ timeout: 45_000 });
		await expect(rowJourneyLink).toHaveAttribute('href', new RegExp(WORKS_JOURNEY_CODE));

		await row.click();

		await expect(page.getByTestId('pp-detail-panel')).toBeVisible({ timeout: 45_000 });
		const detailStrip = page.getByTestId('pp-detail-procurement-journey');
		await expect(detailStrip).toBeVisible({ timeout: 45_000 });
		const detailLink = page.getByTestId('pp-detail-journey-open-link');
		await expect(detailLink).toHaveAttribute('href', new RegExp(WORKS_JOURNEY_CODE));
		await expect(detailStrip).toContainText(/District Hospital Renovation Works/i);
	});
});
