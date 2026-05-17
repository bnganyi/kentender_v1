/**
 * R6-006 / LV-R6-006-01 — Ordinary procurement user: business readiness story is visible
 * first; technical STD output codes stay in the collapsed drawer (pack §12.6).
 *
 * Uses the **TM2 Tender Desk form** (`tm2-tender` …) with `loginAsProcurementOfficer`: the
 * Management v2 **workbench** page is often role-gated, while the same
 * `BusinessReadinessSummary` mount is available on the form for users with TM2 read (R6-002).
 *
 * Companion: docs/prompts/0. usability handoff/R6_006_ordinary_user_business_first_evidence.md
 */
import { expect, test } from '@playwright/test';

import { loginAsProcurementOfficer } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('Ordinary procurement user — business readiness first (R6-006)', () => {
	test.setTimeout(180_000);

	test('PLC-R6-006-01: Procurement Officer sees business labels before technical drawer', async ({
		page,
	}) => {
		await loginAsProcurementOfficer(page);

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

		const br = page.getByTestId('plc-business-readiness-summary');
		await expect(br).toBeVisible({ timeout: 90_000 });

		await expect(host.getByTestId('plc-br-loading')).toHaveCount(0);

		await expect(br.getByTestId('plc-br-summary-label')).toContainText(/Tender document readiness/i, {
			timeout: 30_000,
		});

		await expect(br.getByTestId('plc-br-business-label').first()).toContainText(
			/Tender document package ready/i,
			{ timeout: 30_000 },
		);

		const techDetails = br.getByTestId('plc-br-technical-collapsed');
		await expect(techDetails).toBeVisible();
		await expect(techDetails).not.toHaveAttribute('open');

		await expect(br.getByTestId('plc-technical-evidence-body')).not.toBeVisible();

		const businessFirst = await br.evaluate((rootEl) => {
			const checks = rootEl.querySelector('[data-testid="plc-br-business-checks"]');
			const tech = rootEl.querySelector('[data-testid="plc-br-technical-collapsed"]');
			if (!checks || !tech) {
				return false;
			}
			return Boolean(checks.compareDocumentPosition(tech) & Node.DOCUMENT_POSITION_FOLLOWING);
		});
		expect(businessFirst).toBe(true);
	});
});
