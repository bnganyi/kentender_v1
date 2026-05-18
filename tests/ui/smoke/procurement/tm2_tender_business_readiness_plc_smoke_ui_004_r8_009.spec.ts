/**
 * R8-009 / LV-R8-UI-04 / PLC-SMOKE-UI-004 — TM2 Tender form: business readiness labels first;
 * technical STD codes only after expanding the drawer (pack §15.2).
 *
 * Builds on R6-001 / R6-002 / R6-003; uses WORKS tender `TND-MOH-2026-001`.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { expectPlcSmokeUi004Tm2TenderFormBusinessReadiness } from '../../helpers/procurement';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('PLC-SMOKE-UI-004 TM2 business readiness (R8-009)', () => {
	test.setTimeout(180_000);

	test('PLC-SMOKE-UI-004: plc-business-readiness-summary shows five pack labels; technical hidden until expand', async ({
		page,
	}) => {
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
		await expectPlcSmokeUi004Tm2TenderFormBusinessReadiness(page);
	});
});
