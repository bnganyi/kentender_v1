/**
 * P10-06 — Supplier Works BOQ (doc 9 §18.6): quantity read-only; rate inputs where DSM allows;
 * negative rates rejected via min=0 + validation (items 6–7).
 *
 * Canonical doc 9 §21.3 Q-04: ``tests/ui/tm2_supplier_boq.spec.ts``.
 *
 * Requires seeded tender + supplier profile on the target site. Set:
 *   UI_SUPPLIER_PORTAL_USER
 *   UI_SUPPLIER_PORTAL_BOQ_TENDER  (tender_code with Works BOQ + DSM rate entry)
 */
import { expect, test } from '@playwright/test';

import { loginAsSupplierPortalUser } from '../../helpers/auth';

test.describe('Supplier portal Works BOQ (P10-06)', () => {
	test.setTimeout(120_000);

	test('BOQ quantity is not an input; rate row has min 0 when BOQ tender env is set', async ({ page, baseURL }) => {
		const user = process.env.UI_SUPPLIER_PORTAL_USER;
		const tcode = process.env.UI_SUPPLIER_PORTAL_BOQ_TENDER;
		if (!user || !tcode) {
			test.skip();
			return;
		}
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await loginAsSupplierPortalUser(page);
		await page.goto(`${root}/supplier/tenders/${encodeURIComponent(tcode)}`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
		const denied = page.getByRole('alert');
		const okHeader = page.getByTestId('tm2-supplier-server-time');
		await expect(denied.or(okHeader).first()).toBeVisible({ timeout: 60_000 });
		if (await denied.isVisible().catch(() => false)) {
			return;
		}
		const editor = page.getByTestId('tm2-supplier-works-boq-editor');
		await expect(editor).toBeVisible();
		const qty = editor.getByTestId('tm2-supplier-boq-quantity').first();
		await expect(qty).toBeVisible();
		await expect(qty.locator('input')).toHaveCount(0);
		const rateInp = editor.getByTestId('tm2-supplier-boq-rate-input').first();
		if ((await rateInp.count()) > 0) {
			await expect(rateInp).toHaveAttribute('min', '0');
			await rateInp.fill('-10');
			const v = await rateInp.evaluate((el: HTMLInputElement) => el.validity.valid);
			expect(v, 'negative rate should fail constraint validation').toBe(false);
		}
	});
});
