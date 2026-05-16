/**
 * R5-002 / LV-R5-002-01 — Procurement Journey Impact panel on Strategy forms AND Strategy Builder.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';
const OBJ_CODE = 'OBJ-MOH-HOSP-RENOV';

test.describe('Procurement journey impact panel (R5-002)', () => {
	test('PLC-R5-002-01: Strategy Objective shows WORKS journey deep link', async ({ page }) => {
		await loginAsAdministrator(page);

		const objName = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<string | null>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Strategy Objective',
						filters: [['objective_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: Array<{ name?: string }> }) =>
						resolve(r.message?.[0]?.name ?? null),
					error: reject,
				});
			});
		}, OBJ_CODE);

		if (!objName) {
			test.skip(true, 'WORKS Strategy Objective not on site.');
		}

		await page.goto(
			`/app/strategy-objective/${encodeURIComponent(objName!)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		const panel = page.getByTestId('plc-strategy-procurement-journey-impact');
		await expect(panel).toBeVisible({ timeout: 60_000 });

		await expect(page.getByTestId('plc-strategy-procurement-journey-impact-journeys')).toBeVisible({
			timeout: 60_000,
		});
		await expect(
			page.getByTestId('plc-strategy-procurement-journey-impact-journey-title'),
		).toContainText(/District Hospital|Renovation/i, { timeout: 30_000 });

		const journeyLink = page
			.getByTestId('plc-strategy-procurement-journey-impact-journey-row')
			.getByRole('link')
			.first();
		await expect(journeyLink).toHaveAttribute('href', new RegExp(WORKS_JOURNEY_CODE));
	});

	test('PLC-R5-002-02: Strategy Target shows linked budget line row', async ({ page }) => {
		await loginAsAdministrator(page);

		const tgtName = await page.evaluate(async (code) => {
			// @ts-ignore desk frappe
			return await new Promise<string | null>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Strategy Target',
						filters: [['target_code', '=', code]],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: Array<{ name?: string }> }) =>
						resolve(r.message?.[0]?.name ?? null),
					error: reject,
				});
			});
		}, 'TGT-MOH-HOSP-RENOV-2026');

		if (!tgtName) {
			test.skip(true, 'WORKS Strategy Target not on site.');
		}

		await page.goto(`/app/strategy-target/${encodeURIComponent(tgtName!)}`, {
			waitUntil: 'domcontentloaded',
		});

		const panel = page.getByTestId('plc-strategy-procurement-journey-impact');
		await expect(panel).toBeVisible({ timeout: 60_000 });

		await expect(
			page.getByTestId('plc-strategy-procurement-journey-impact-budget-lines'),
		).toBeVisible({ timeout: 60_000 });
		const budRow = page.getByTestId('plc-strategy-procurement-journey-impact-budget-row').first();
		await expect(budRow).toContainText('BUD-MOH-INFRA-2026-001');
	});

	test('PLC-R5-002-03: Strategy Builder inline detail shows Procurement Journey Impact for Objective', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		// Resolve the WORKS strategic plan name
		const planName = await page.evaluate(async (objCode) => {
			// @ts-ignore desk frappe
			return await new Promise<string | null>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Strategy Objective',
						filters: [['objective_code', '=', objCode]],
						fields: ['name', 'strategic_plan'],
						limit_page_length: 1,
					},
					callback: (r: { message?: Array<{ name?: string; strategic_plan?: string }> }) =>
						resolve(r.message?.[0]?.strategic_plan ?? null),
					error: reject,
				});
			});
		}, OBJ_CODE);

		if (!planName) {
			test.skip(true, 'WORKS Strategic Plan not on site.');
		}

		await page.goto(`/desk/strategy-builder/${encodeURIComponent(planName!)}`, {
			waitUntil: 'domcontentloaded',
		});

		// Click on the WORKS Objective in the tree
		const objRow = page.getByText(/Improve district hospital infrastructure/i).first();
		await expect(objRow).toBeVisible({ timeout: 30_000 });
		await objRow.click();

		// Procurement Journey Impact section should appear in the editor panel
		const panel = page.getByTestId('plc-strategy-procurement-journey-impact');
		await expect(panel).toBeVisible({ timeout: 30_000 });

		// Journeys section loads with WORKS journey
		await expect(
			page.getByTestId('plc-strategy-procurement-journey-impact-journeys'),
		).toBeVisible({ timeout: 30_000 });
		await expect(
			page.getByTestId('plc-strategy-procurement-journey-impact-journey-title').first(),
		).toContainText(/District Hospital|Renovation/i, { timeout: 30_000 });

		// Journey link points to PLC page
		const journeyLink = page
			.getByTestId('plc-strategy-procurement-journey-impact-journey-row')
			.getByRole('link')
			.first();
		await expect(journeyLink).toHaveAttribute('href', new RegExp(WORKS_JOURNEY_CODE));
	});
});
