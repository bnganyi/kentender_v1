/**
 * R5-007 / LV-R5-007-01 — Planning workbench package detail shows §11.5 business readiness checklist.
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

test.describe('Procurement Planning business readiness checklist (R5-007)', () => {
	test('PLC-R5-007-01: WORKS package shows eight readiness checks with PASS', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const seedOk = await page.evaluate(async ({ pkg, tmHint }) => {
			// @ts-ignore desk frappe
			const hasPkg = await new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Procurement Package',
						filters: [['package_code', '=', pkg]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
					error: reject,
				});
			});
			if (!hasPkg) return false;
			const hasTm = await new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'TM2 Tender',
						filters: [['procurement_package_code', '=', tmHint]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
					error: reject,
				});
			});
			return hasTm;
		}, { pkg: PKG_CODE, tmHint: PKG_CODE });

		test.skip(!seedOk, 'WORKS package + TM2 link not on site.');

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
		await row.click();

		await expect(page.getByTestId('pp-detail-panel')).toBeVisible({ timeout: 45_000 });

		const readiness = page.getByTestId('pp-detail-business-readiness');
		await expect(readiness).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('pp-detail-readiness-summary')).toContainText(/All checks pass/i);

		const expectedIds = [
			'scope_ready',
			'budget_linked',
			'demand_approved',
			'procurement_method_selected',
			'procurement_category_selected',
			'std_category_identified',
			'package_released',
			'tender_created',
		];

		for (const id of expectedIds) {
			const rowLocator = page.getByTestId(`pp-detail-readiness-${id}`);
			await expect(rowLocator).toBeVisible({ timeout: 45_000 });
			await expect(rowLocator).toContainText(/Pass/i);
		}
	});
});
