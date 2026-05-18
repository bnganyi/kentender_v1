/**
 * R8-011 / LV-R8-UI-06 / PLC-SMOKE-UI-006 — TM2 Tender detail shows Procurement Journey context header.
 *
 * Pack §15.2 selector `plc-module-journey-context-header`; expected WORKS journey context copy.
 *
 * Depends on **R5-010 / LV-R5-010-01** Desk wiring.
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { expectPlcSmokeUi006Tm2ModuleJourneyContextHeader } from '../../helpers/procurement';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

async function tenderSeedExists(page: Page, code: string): Promise<boolean> {
	return page.evaluate(async (tenderCode) => {
		return new Promise<boolean>((resolve, reject) => {
			// @ts-ignore desk frappe
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'TM2 Tender',
					filters: [['tender_code', '=', tenderCode]],
					fields: ['name'],
					limit_page_length: 1,
				},
				callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
				error: reject,
			});
		});
	}, code);
}

test.describe('PLC-SMOKE-UI-006 module journey context on TM2 (R8-011)', () => {
	test.setTimeout(180_000);

	test('PLC-SMOKE-UI-006: plc-module-journey-context-header shows WORKS District Hospital journey', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const seedOk = await tenderSeedExists(page, WORKS_TENDER_CODE);
		test.skip(!seedOk, `TM2 Tender ${WORKS_TENDER_CODE} missing on site.`);

		await page.goto(`/app/tm2-tender/${encodeURIComponent(WORKS_TENDER_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await dismissOptionalDeskModals(page);

		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 90_000 });
		await expectPlcSmokeUi006Tm2ModuleJourneyContextHeader(page);
	});
});
