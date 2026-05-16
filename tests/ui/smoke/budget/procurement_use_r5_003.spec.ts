/**
 * R5-003 / LV-R5-003-01 — Procurement Use panel on Budget Line form.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

const WORKS_BL_CODE = 'BUD-MOH-INFRA-2026-001';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';
const WORKS_DEMAND_ID = 'DEM-MOH-2026-001';
const WORKS_PKG_CODE = 'PKG-MOH-2026-001';
const WORKS_BUDGET_NAME = 'BUDGET-MOH-2026';

test.describe('Procurement use panel on Budget Line (R5-003)', () => {
	test('PLC-R5-003-01: Budget Line shows Procurement Use panel with funding confirmation', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		// Resolve Budget Line doc name from business code
		const blName = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<string | null>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Budget Line',
						filters: [['budget_line_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: Array<{ name?: string }> }) =>
						resolve(r.message?.[0]?.name ?? null),
					error: reject,
				});
			});
		}, WORKS_BL_CODE);

		if (!blName) {
			test.skip(true, 'WORKS Budget Line not on site.');
		}

		await page.goto(`/app/budget-line/${encodeURIComponent(blName!)}`, {
			waitUntil: 'domcontentloaded',
		});

		// Root panel visible
		const panel = page.getByTestId('plc-budget-procurement-use');
		await expect(panel).toBeVisible({ timeout: 60_000 });

		// Funding confirmation section visible
		const funding = page.getByTestId('plc-budget-procurement-use-funding');
		await expect(funding).toBeVisible({ timeout: 30_000 });
		await expect(funding).toContainText(WORKS_BUDGET_NAME);

		// Amounts present
		await expect(
			page.getByTestId('plc-budget-procurement-use-amount-allocated'),
		).toBeVisible({ timeout: 15_000 });
	});

	test('PLC-R5-003-02: Budget Line shows WORKS journey, demand, and package links', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const blName = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<string | null>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Budget Line',
						filters: [['budget_line_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: Array<{ name?: string }> }) =>
						resolve(r.message?.[0]?.name ?? null),
					error: reject,
				});
			});
		}, WORKS_BL_CODE);

		if (!blName) {
			test.skip(true, 'WORKS Budget Line not on site.');
		}

		await page.goto(`/app/budget-line/${encodeURIComponent(blName!)}`, {
			waitUntil: 'domcontentloaded',
		});

		const panel = page.getByTestId('plc-budget-procurement-use');
		await expect(panel).toBeVisible({ timeout: 60_000 });

		// Journeys section
		await expect(
			page.getByTestId('plc-budget-procurement-use-journeys'),
		).toBeVisible({ timeout: 30_000 });

		const journeyTitle = page
			.getByTestId('plc-budget-procurement-use-journey-title')
			.first();
		await expect(journeyTitle).toContainText(/District Hospital|Renovation/i, {
			timeout: 30_000,
		});

		// Journey deep link points to PLC journey page
		const journeyLink = page
			.getByTestId('plc-budget-procurement-use-journey-row')
			.getByRole('link')
			.first();
		await expect(journeyLink).toHaveAttribute('href', new RegExp(WORKS_JOURNEY_CODE));

		// Demands section
		await expect(
			page.getByTestId('plc-budget-procurement-use-demands'),
		).toBeVisible({ timeout: 30_000 });
		await expect(
			page.getByTestId('plc-budget-procurement-use-demand-row').first(),
		).toContainText(WORKS_DEMAND_ID);

		// Packages section
		await expect(
			page.getByTestId('plc-budget-procurement-use-packages'),
		).toBeVisible({ timeout: 30_000 });
		await expect(
			page.getByTestId('plc-budget-procurement-use-package-row').first(),
		).toContainText(WORKS_PKG_CODE);
	});
});
