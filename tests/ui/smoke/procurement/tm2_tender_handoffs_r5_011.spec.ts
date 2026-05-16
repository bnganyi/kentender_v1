/**
 * R5-011 — TM2 Tender desk form: Procurement hand-offs panel (PKGREL / STD ready / Publication).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const WORKS_TENDER_CODE = 'TND-MOH-2026-001';

test.describe('TM2 Tender form procurement hand-offs (R5-011)', () => {
	test('PLC-R5-011-01: WORKS TM2 lists planning release + STD readiness + publication', async ({
		page,
	}) => {
		await loginAsAdministrator(page);

		const seedOk = await page.evaluate(async (code) => {
			const hasTm = await new Promise<boolean>((resolve, reject) => {
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
			if (!hasTm) return false;
			const hasHp = await new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method: 'frappe.client.get_list',
					args: {
						doctype: 'Procurement Handoff Card',
						filters: [['handoff_code', '=', 'PKGREL-MOH-2026-001']],
						fields: ['name'],
						limit_page_length: 1,
					},
					callback: (r: { message?: unknown[] }) => resolve(!!r.message?.length),
					error: reject,
				});
			});
			return hasHp;
		}, WORKS_TENDER_CODE);

		test.skip(!seedOk, 'WORKS TM2 / PKGREL hand-off seed not on site.');

		await page.goto(`/app/tm2-tender/${encodeURIComponent(WORKS_TENDER_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await dismissOptionalDeskModals(page);

		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 90_000 });

		const shell = page.getByTestId('tm2-tender-handoff-panel');
		await expect(shell).toBeVisible({ timeout: 45_000 });
		await expect(shell.getByTestId('tm2-handoff-rows-table')).toBeVisible({ timeout: 45_000 });

		const pkg = shell.locator(
			'[data-testid="tm2-handoff-row"][data-handoff-code="PKGREL-MOH-2026-001"]',
		);
		await expect(pkg).toBeVisible({ timeout: 45_000 });
		await expect(pkg.getByTestId('tm2-handoff-row-status')).toContainText(/Consumed/i);

		const std = shell.locator(
			'[data-testid="tm2-handoff-row"][data-handoff-code="STDREADY-TND-MOH-2026-001"]',
		);
		await expect(std).toBeVisible({ timeout: 45_000 });
		await expect(std.getByTestId('tm2-handoff-row-title')).toContainText(
			/Tender Document Readiness Certificate/i,
		);

		const pub = shell.locator(
			'[data-testid="tm2-handoff-row"][data-handoff-code="PUBCERT-TND-MOH-2026-001"]',
		);
		await expect(pub).toBeVisible({ timeout: 45_000 });
		await expect(pub.getByTestId('tm2-handoff-row-status')).toContainText(/handed\s*off/i);
		await expect(pub.getByTestId('tm2-handoff-row-open')).toBeVisible();
	});

	test('PLC-R5-011-02: optional checkbox requests extended hand-offs payload', async ({ page }) => {
		await loginAsAdministrator(page);

		const seedOk = await page.evaluate(async (code) => {
			const tm = await new Promise<boolean>((resolve, reject) => {
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
			if (!tm) return false;
			return new Promise<boolean>((resolve, reject) => {
				// @ts-ignore desk frappe
				frappe.call({
					method:
						'kentender_procurement.procurement_lifecycle.api.journey_api.get_tm2_handoff_panel',
					args: { tender_code: code, include_optional_opening: 1 },
					callback: (r: { exc?: unknown; message?: { handoffs?: { handoff_code: string }[] } }) => {
						if (r.exc) {
							resolve(false);
							return;
						}
						const codes = new Set((r.message?.handoffs || []).map((h) => h.handoff_code));
						resolve(codes.has('CLOSECERT-TND-MOH-2026-001'));
					},
					error: reject,
				});
			});
		}, WORKS_TENDER_CODE);

		test.skip(!seedOk, 'OPENING_READY CLOSECERT hand-off not available on site.');

		await page.goto(`/app/tm2-tender/${encodeURIComponent(WORKS_TENDER_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		await dismissOptionalDeskModals(page);

		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 90_000 });

		const chk = page.getByTestId('tm2-handoff-include-optional');
		await chk.waitFor({ state: 'visible', timeout: 45_000 });
		await chk.setChecked(true, { timeout: 10_000 });

		const closer = page.locator(
			'[data-testid="tm2-handoff-row"][data-handoff-code="CLOSECERT-TND-MOH-2026-001"]',
		);
		await expect(closer).toBeVisible({ timeout: 45_000 });
		await expect(closer.getByTestId('tm2-handoff-row-status')).toContainText(/Consumed/i);
	});
});
