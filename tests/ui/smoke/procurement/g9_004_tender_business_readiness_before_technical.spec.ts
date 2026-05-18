/**
 * §14 G9-004 — Tender complexity reduced on **TM2 Tender**: **business readiness** labels appear
 * before technical STD outputs (technical section collapsed until expanded).
 *
 * Reuses **PLC-SMOKE-UI-004 / R8-009** helper contract (`expectPlcSmokeUi004Tm2TenderFormBusinessReadiness`).
 * Requires WORKS tender **`TND-MOH-2026-001`**.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { expectPlcSmokeUi004Tm2TenderFormBusinessReadiness } from '../../helpers/procurement';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('G9-004 Tender business readiness before technical outputs', () => {
	test.setTimeout(180_000);

	test('G9-004: TM2 form shows five business labels first; technical codes after expand only', async ({
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
