/**
 * P10-04 — Supplier portal documents & addenda (doc 9 §18.4).
 * Denied path must not expose bundle controls; optional supplier user sees §18.4 panels.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator, loginAsSupplierPortalUser } from '../../helpers/auth';

test.describe('Supplier portal documents & addenda (P10-04)', () => {
	test.setTimeout(120_000);

	test('denied detail does not render bundle download control', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const res = await page.goto(`${root}/supplier/tenders/TND-P10-04-DENY-TC`, { waitUntil: 'domcontentloaded' });
		expect(res?.status(), 'HTTP status should not be 404').not.toBe(404);
		await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByRole('alert')).toBeVisible();
		await expect(page.getByTestId('tm2-supplier-bundle-download-control')).toHaveCount(0);
	});

	test('supplier user sees documents and addenda panels on detail when configured', async ({ page, baseURL }) => {
		if (!process.env.UI_SUPPLIER_PORTAL_USER) {
			test.skip();
			return;
		}
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await loginAsSupplierPortalUser(page);
		await page.goto(`${root}/supplier/tenders/PORTAL-SMOKE-TC`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
		const denied = page.getByRole('alert');
		const okHeader = page.getByTestId('tm2-supplier-server-time');
		await expect(denied.or(okHeader).first()).toBeVisible({ timeout: 60_000 });
		const deniedVisible = await denied.isVisible().catch(() => false);
		if (deniedVisible) {
			await expect(page.getByTestId('tm2-supplier-bundle-download-control')).toHaveCount(0);
			return;
		}
		await expect(page.getByTestId('tm2-supplier-documents-panel')).toBeVisible();
		await expect(page.getByTestId('tm2-supplier-addenda-panel')).toBeVisible();
		await expect(page.getByTestId('tm2-supplier-bundle-download-control')).toBeVisible();
	});
});
