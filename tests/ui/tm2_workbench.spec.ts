/**
 * Q-01 — doc 9 §21.3 items 1–2 (canonical `tm2_workbench.spec.ts`).
 *
 * 1. Workbench route loads `tm2-workbench-page`.
 * 2. Queue bar contains `tm2-queue-std-incomplete`.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from './helpers/auth';
import { dismissOptionalDeskModals } from './helpers/routes';

test.describe('TM2 workbench (Q-01 / doc 9 §21.3)', () => {
	test.setTimeout(180_000);

	test('§21.3 (1) — /app/tender-management-v2 loads tm2-workbench-page', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await expect(page.getByTestId('tm2-workbench-page')).toBeVisible({ timeout: 90_000 });
	});

	test('§21.3 (2) — queue bar contains tm2-queue-std-incomplete', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const bar = shell.getByTestId('tm2-queue-bar');
		await expect(bar).toBeVisible({ timeout: 60_000 });
		await expect(bar.getByTestId('tm2-queue-std-incomplete')).toBeVisible();
	});
});
