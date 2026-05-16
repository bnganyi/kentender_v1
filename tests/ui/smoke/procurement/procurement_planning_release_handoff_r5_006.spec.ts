/**
 * R5-006 / LV-R5-006-01 — Planning workbench package detail shows Planning Release handoff + linked tender.
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
const EXPECTED_HANDOFF_CODE = 'PKGREL-MOH-2026-001';
const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('Procurement Planning planning release handoff (R5-006)', () => {
	test('PLC-R5-006-01: WORKS package row and detail expose linked tender from PKGREL', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const hasCard = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Procurement Handoff Card',
						filters: [['handoff_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
					error: reject,
				});
			});
		}, EXPECTED_HANDOFF_CODE);
		test.skip(!hasCard, `WORKS handoff ${EXPECTED_HANDOFF_CODE} not on site.`);

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

		const rowHandoff = page.getByTestId(`pp-row-planning-release-${PKG_ROW_SLUG}`);
		await expect(rowHandoff).toBeVisible({ timeout: 45_000 });
		await expect(rowHandoff).toContainText(WORKS_TENDER_CODE);

		await row.click();

		await expect(page.getByTestId('pp-detail-panel')).toBeVisible({ timeout: 45_000 });
		const handoffBlock = page.getByTestId('pp-detail-planning-release-handoff');
		await expect(handoffBlock).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('pp-detail-pr-handoff-code')).toContainText(
			new RegExp(EXPECTED_HANDOFF_CODE),
		);
		await expect(page.getByTestId('pp-detail-pr-status')).toContainText(/Consumed/i);

		const tenderOpen = page.getByTestId('pp-detail-pr-tender-open');
		await expect(tenderOpen).toBeVisible({ timeout: 45_000 });
		await expect(tenderOpen).toHaveAttribute('href', /tm2-tender/i);
		await expect(tenderOpen).toContainText(new RegExp(WORKS_TENDER_CODE));
	});
});
