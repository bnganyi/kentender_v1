/**
 * P10-02 — Supplier portal tender list (doc 9 §18.2).
 * Logged-in desk user without KTSM profile sees empty-state shell (no leaked rows).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('Supplier portal tender list (P10-02)', () => {
	test.setTimeout(120_000);

	test('list page shows empty state for user without supplier profile', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const res = await page.goto(`${root}/supplier/tenders`, { waitUntil: 'domcontentloaded' });
		expect(res?.status(), 'HTTP status should not be 404').not.toBe(404);
		await expect(page.getByTestId('tm2-supplier-tender-list')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('tm2-supplier-portal-empty')).toBeVisible();
		await expect(page.getByTestId('tm2-supplier-tender-list-table')).toHaveCount(0);
	});
});
