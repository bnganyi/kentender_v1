/**
 * P10-01 — Supplier portal routes (doc 9 §18.1).
 * `/supplier/tenders` and `/supplier/tenders/:tender_code` must render the TM2 shell (no 404 on happy path).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('Supplier portal routes (P10-01)', () => {
	test.setTimeout(120_000);

	test('list URL shows tm2-supplier-tender-list when logged in', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const res = await page.goto(`${root}/supplier/tenders`, { waitUntil: 'domcontentloaded' });
		expect(res?.status(), 'HTTP status should not be 404').not.toBe(404);
		await expect(page.getByTestId('tm2-supplier-tender-list')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('tm2-supplier-tender-list-tabs')).toBeVisible();
	});

	test('detail URL shows tm2-supplier-tender-detail when logged in', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const code = 'P10-01-ROUTE-TC';
		const res = await page.goto(`${root}/supplier/tenders/${code}`, { waitUntil: 'domcontentloaded' });
		expect(res?.status(), 'HTTP status should not be 404').not.toBe(404);
		await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('tm2-supplier-tender-detail-header')).toBeVisible();
		await expect(page.getByTestId('tm2-supplier-tender-detail-header')).toContainText(code);
	});
});
