/**
 * R6-002 / LV-R6-002-01 — TM2 Tender Desk form: `BusinessReadinessSummary.mount`
 * uses `read_business_readiness_summary` (loading + success/error end states).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('TM2 Tender form business readiness API mount (R6-002)', () => {
	test.setTimeout(180_000);

	test('PLC-R6-002-01: form host resolves readiness card after load', async ({ page }) => {
		await loginAsAdministrator(page);

		const seedOk = await page.evaluate(async (code) => {
			return new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'TM2 Tender',
						filters: [['tender_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
					error: reject,
				});
			});
		}, WORKS_TENDER_CODE);

		test.skip(!seedOk, `TM2 Tender ${WORKS_TENDER_CODE} missing on site.`);

		await page.goto(`/app/tm2-tender/${encodeURIComponent(WORKS_TENDER_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await dismissOptionalDeskModals(page);

		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 90_000 });

		const host = page.getByTestId('tm2-tender-business-readiness-host');
		await expect(host).toBeVisible({ timeout: 45_000 });

		const summary = page.getByTestId('plc-business-readiness-summary');
		await expect(summary).toBeVisible({ timeout: 90_000 });

		await expect(host.getByTestId('plc-br-loading')).toHaveCount(0);

		await expect(summary.getByTestId('plc-br-status')).toBeVisible();
	});
});
