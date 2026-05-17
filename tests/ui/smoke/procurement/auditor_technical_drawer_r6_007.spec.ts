/**
 * R6-007 / LV-R6-007-01 — Auditor can expand the business-readiness technical drawer and
 * view STD output references (Bundle / DSM / …), aligned with pack §12.6 “auditor can still
 * open full STD technical evidence”.
 *
 * Uses the TM2 Tender Desk form (`/app/tm2-tender/…`) for role-stable access (same pattern
 * as R6-006 when workbench routing differs by role).
 *
 * Companion: docs/prompts/0. usability handoff/R6_007_auditor_technical_view_evidence.md
 */
import { expect, test } from '@playwright/test';

import { loginAsAuditor } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('Auditor — technical readiness drawer (R6-007)', () => {
	test.setTimeout(180_000);

	test('PLC-R6-007-01: Auditor opens technical drawer and sees output lines or empty-tech notice', async ({
		page,
	}) => {
		await loginAsAuditor(page);

		const readable = await page.evaluate(async (code) => {
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

		test.skip(!readable, 'Auditor cannot read seeded TM2 Tender — skip UI (permissions/seed).');

		await page.goto(`/app/tm2-tender/${encodeURIComponent(WORKS_TENDER_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await dismissOptionalDeskModals(page);

		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 90_000 });

		await expect(page.getByTestId('tm2-tender-business-readiness-host')).toBeVisible({
			timeout: 45_000,
		});

		const br = page.getByTestId('plc-business-readiness-summary');
		await expect(br).toBeVisible({ timeout: 90_000 });

		await expect(br.getByTestId('plc-br-technical-restricted')).toHaveCount(0);

		const body = br.getByTestId('plc-technical-evidence-body');
		await expect(body).not.toBeVisible();

		await br.getByTestId('plc-br-technical-summary').click({ timeout: 15_000 });
		await expect(br.locator('details.plc-tm2-readiness-technical-drawer')).toHaveAttribute('open');

		await expect(body).toBeVisible({ timeout: 15_000 });

		const techLines = br.getByTestId('plc-br-technical-line');
		const lineCount = await techLines.count();
		if (lineCount > 0) {
			await expect(techLines.first().locator('.plc-technical-output-code')).toBeVisible();
		} else {
			await expect(br.getByTestId('plc-br-no-tech')).toBeVisible();
		}
	});
});
