/**
 * R5-004 / LV-R5-004-01 — Procurement planning handoff in DIA detail (primary surface).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

const WORKS_DEMAND_ID = 'DEM-MOH-2026-001';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('Demand planning handoff — DIA (R5-004)', () => {
	test('PLC-R5-004-01: Approved WORKS demand shows PLC handoff section and certificate link', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const demandName = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<string | null>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Demand',
						filters: [['demand_id', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: Array<{ name?: string }> }) =>
						resolve(r.message?.[0]?.name ?? null),
					error: reject,
				});
			});
		}, WORKS_DEMAND_ID);
		test.skip(!demandName, 'WORKS Demand (DEM-MOH-2026-001) not on site — seed procurement lifecycle fixtures.');

		await openDIALanding(page);

		await page.getByTestId('dia-tab-all').click({ timeout: 15_000 });
		await page.getByTestId('dia-queue-all_demands').click({ timeout: 15_000 });

		await page.getByTestId('dia-search-input').fill(WORKS_DEMAND_ID);

		const row = page.locator(`[data-dia-demand="${demandName as string}"]`);
		await expect(row).toBeVisible({ timeout: 45_000 });
		await row.click();

		await expect(page.getByTestId('dia-detail-panel')).toBeVisible({ timeout: 30_000 });

		const section = page.getByTestId('dia-detail-section-planning-handoff');
		await expect(section).toBeVisible({ timeout: 30_000 });

		await expect(page.getByTestId('dia-detail-planning-handoff-subtitle')).toContainText(WORKS_DEMAND_ID);

		await expect(page.getByTestId('dia-detail-planning-handoff-journey')).toBeVisible({
			timeout: 30_000,
		});

		const jLink = page.getByTestId('dia-detail-planning-handoff-journey-link').first();
		await expect(jLink).toHaveAttribute('href', new RegExp(WORKS_JOURNEY_CODE));

		await expect(page.getByTestId('dia-detail-planning-handoff-certificate')).toBeVisible({
			timeout: 30_000,
		});

		await expect(page.getByTestId('dia-detail-planning-handoff-certificate-link')).toBeVisible();
		await expect(page.getByTestId('dia-detail-planning-handoff-certificate-link')).toContainText(
			/Demand Approval Record/i,
		);

		await expect(page.getByTestId('dia-detail-planning-handoff-planning-inclusion')).toBeVisible({
			timeout: 30_000,
		});

		await expect(page.getByTestId('dia-detail-planning-handoff-plan-code')).toContainText(
			/PLAN-MOH-2026/,
			{ timeout: 15_000 },
		);
	});
});
