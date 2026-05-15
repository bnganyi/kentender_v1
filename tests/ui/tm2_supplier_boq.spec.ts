/**
 * Q-04 — doc 9 §21.3 items 6–7 (canonical `tm2_supplier_boq.spec.ts`).
 *
 * 6. Supplier Works BOQ editor **locks quantity** (no `<input>` in quantity cells).
 * 7. Supplier Works BOQ editor **allows rate** cells (`tm2-supplier-boq-rate-input` enabled for DSM rate entry).
 *
 * Requires ``UI_SUPPLIER_PORTAL_USER`` and ``UI_SUPPLIER_PORTAL_BOQ_TENDER`` (Works tender with BOQ rate entry).
 * See ``tests/ui/smoke/procurement/tender-management-v2-supplier-boq-p10-06.spec.ts`` (P10-06).
 */
import { expect, test } from '@playwright/test';

import { loginAsSupplierPortalUser } from './helpers/auth';

async function openSupplierBoqEditor(page: import('@playwright/test').Page, baseURL: string | undefined) {
	const user = (process.env.UI_SUPPLIER_PORTAL_USER || '').trim();
	const tcode = (process.env.UI_SUPPLIER_PORTAL_BOQ_TENDER || '').trim();
	if (!user || !tcode) {
		test.skip(true, 'Set UI_SUPPLIER_PORTAL_USER and UI_SUPPLIER_PORTAL_BOQ_TENDER (see .env.ui).');
	}
	const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
	await loginAsSupplierPortalUser(page);
	await page.goto(`${root}/supplier/tenders/${encodeURIComponent(tcode)}`, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
	const denied = page.getByRole('alert');
	const okHeader = page.getByTestId('tm2-supplier-server-time');
	await expect(denied.or(okHeader).first()).toBeVisible({ timeout: 60_000 });
	if (await denied.isVisible().catch(() => false)) {
		test.skip(true, 'Supplier portal denied or tender not available for this user.');
	}
	const editor = page.getByTestId('tm2-supplier-works-boq-editor');
	await expect(editor).toBeVisible({ timeout: 60_000 });
	return editor;
}

test.describe('TM2 supplier BOQ (Q-04 / doc 9 §21.3)', () => {
	test.setTimeout(120_000);

	test('§21.3 (6) — quantity cells are read-only (no input)', async ({ page, baseURL }) => {
		const editor = await openSupplierBoqEditor(page, baseURL);
		const qty = editor.getByTestId('tm2-supplier-boq-quantity').first();
		await expect(qty).toBeVisible();
		await expect(qty.locator('input')).toHaveCount(0);
	});

	test('§21.3 (7) — rate cells are editable where DSM exposes rate entry', async ({ page, baseURL }) => {
		const editor = await openSupplierBoqEditor(page, baseURL);
		const rateInp = editor.getByTestId('tm2-supplier-boq-rate-input').first();
		if ((await rateInp.count()) === 0) {
			test.skip(true, 'No rate inputs on this tender (no BOQRateEntry / rate-only lines).');
		}
		await expect(rateInp).toBeVisible();
		await expect(rateInp).toBeEnabled();
		await expect(rateInp).toHaveAttribute('min', '0');
		await rateInp.fill('-10');
		const invalid = await rateInp.evaluate((el: HTMLInputElement) => el.validity.valid);
		expect(invalid, 'negative rate should fail HTML constraint validation').toBe(false);
	});
});
