/**
 * R6-004 / LV-R6-004-01 — DEM failure shows `plc-br-dem-blocker` without raw
 * `DEM_MISSING_OR_STALE` as user-facing copy (NEG-TND-MISSING-DEM-001 when seeded).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const NEG_DEM = 'NEG-TND-MISSING-DEM-001';

test.describe('TM2 DEM business-readable blocker (R6-004)', () => {
	test.setTimeout(180_000);

	test('PLC-R6-004-01: DEM row shows user blocker text, not machine code', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const hasTender = await page.evaluate(async (code) => {
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
		}, NEG_DEM);

		test.skip(!hasTender, `TM2 Tender ${NEG_DEM} not on site — load negative fixtures if needed.`);

		await page.goto(`/app/tm2-tender/${encodeURIComponent(NEG_DEM)}`, {
			waitUntil: 'domcontentloaded',
		});
		await dismissOptionalDeskModals(page);

		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 90_000 });

		const demBlock = page.getByTestId('plc-br-dem-blocker');
		await expect(demBlock).toBeVisible({ timeout: 90_000 });
		await expect(demBlock).toContainText(/evaluation/i);
		await expect(demBlock).not.toContainText('DEM_MISSING_OR_STALE');
	});
});
