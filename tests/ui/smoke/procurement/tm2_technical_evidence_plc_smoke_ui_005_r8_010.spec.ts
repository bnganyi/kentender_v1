/**
 * R8-010 / LV-R8-UI-05 / PLC-SMOKE-UI-005 — TM2 Tender readiness: expanding technical drawer
 * shows GB/DSM/DOM/DEM/DCM + publication snapshot (pack §15.2).
 *
 * Aligns with **LV-R6-003-01** readiness expansion behaviour (**`plc-br-technical-collapsed`**).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { expectPlcSmokeUi005Tm2ReadinessTechnicalBodyStdout } from '../../helpers/procurement';
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

test.describe('PLC-SMOKE-UI-005 TM2 technical readiness (R8-010)', () => {
	test.setTimeout(180_000);

	test('PLC-SMOKE-UI-005: expanded plc-technical-evidence-body lists all STD + PUBSNAP tokens', async ({
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
		await expect(page.getByTestId('tm2-tender-business-readiness-host')).toBeVisible({
			timeout: 45_000,
		});

		await expectPlcSmokeUi005Tm2ReadinessTechnicalBodyStdout(page);
	});
});
