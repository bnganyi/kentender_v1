/**
 * Workstream-4 mitigation — Desk smoke for Tender STD Instance list (WORKS-COMP-1200 Playwright slice).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('WORKS WS4 — Tender STD Instance desk shell', () => {
	test('Tender STD Instance list loads for Administrator', async ({ page }) => {
		test.setTimeout(120_000);
		await loginAsAdministrator(page);
		await page.goto('/app/tender-std-instance', { waitUntil: 'domcontentloaded' });
		await expect(page.locator('.list-row-head, .list-row-container, .result').first()).toBeVisible({
			timeout: 90_000,
		});
	});
});
