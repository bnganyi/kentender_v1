import { test, expect } from '@playwright/test';
import { loginAsSupplierPortalUser } from '../../helpers/auth';

test.describe('Supplier portal (Phase O)', () => {
	test('list shell supplier-tender-list when supplier portal user is configured', async ({ page, baseURL }) => {
		if (!process.env.UI_SUPPLIER_PORTAL_USER) {
			test.skip();
			return;
		}
		const root = baseURL || 'http://127.0.0.1:8000';
		await loginAsSupplierPortalUser(page);
		await page.goto(`${root}/supplier/tenders`, { waitUntil: 'domcontentloaded' });
		await expect(page.locator('[data-testid="supplier-tender-list"]')).toBeVisible({ timeout: 60_000 });
		await expect(page.locator('[data-testid="supplier-tender-list-tabs"]')).toBeVisible();
	});

	test('detail shell loads supplier-tender-detail when tender code in route', async ({ page, baseURL }) => {
		if (!process.env.UI_SUPPLIER_PORTAL_USER) {
			test.skip();
			return;
		}
		const root = baseURL || 'http://127.0.0.1:8000';
		await loginAsSupplierPortalUser(page);
		await page.goto(`${root}/supplier/tenders/PORTAL-SMOKE-TC`, { waitUntil: 'domcontentloaded' });
		await expect(page.locator('[data-testid="supplier-tender-detail"]')).toBeVisible({ timeout: 60_000 });
		await expect(page.locator('[data-testid="supplier-tender-detail-header"]')).toBeVisible();
	});
});
