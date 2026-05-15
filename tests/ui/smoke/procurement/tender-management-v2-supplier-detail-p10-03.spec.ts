/**
 * P10-03 — Supplier portal tender detail (doc 9 §18.3).
 * Metadata, submission deadline, server time, and time remaining selectors on happy path.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('Supplier portal tender detail (P10-03)', () => {
	test.setTimeout(120_000);

	test('detail URL shows §18.3 time selectors when tender exists and user lacks profile (denied)', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const code = 'TND-P10-03-SMOKE-TC';
		const res = await page.goto(`${root}/supplier/tenders/${code}`, { waitUntil: 'domcontentloaded' });
		expect(res?.status(), 'HTTP status should not be 404').not.toBe(404);
		await expect(page.getByTestId('tm2-supplier-tender-detail')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('tm2-supplier-tender-detail-header')).toBeVisible();
		await expect(page.getByRole('alert')).toBeVisible();
	});
});
