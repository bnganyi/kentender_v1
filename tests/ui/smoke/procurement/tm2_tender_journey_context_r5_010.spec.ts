/**
 * R5-010 / LV-R5-010-01 — TM2 Tender Desk form: module journey context header.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('TM2 Tender form module journey context (R5-010)', () => {
	test('PLC-R5-010-01: WORKS tender shows journey card on TM2 form', async ({ page }) => {
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

		const shell = page.getByTestId('tm2-tender-module-journey-context');
		await expect(shell).toBeVisible({ timeout: 45_000 });

		const header = shell.getByTestId('plc-module-journey-context-header');
		await expect(header).toBeVisible({ timeout: 45_000 });
		await expect(shell.getByTestId('plc-module-journey-context-title')).toContainText(
			/District Hospital Renovation Works/i,
			{ timeout: 45_000 },
		);
		await expect(shell.getByTestId('plc-module-journey-context-code')).toContainText(
			WORKS_JOURNEY_CODE,
		);
		await expect(shell.getByTestId('plc-module-journey-context-open')).toBeVisible();
	});
});
