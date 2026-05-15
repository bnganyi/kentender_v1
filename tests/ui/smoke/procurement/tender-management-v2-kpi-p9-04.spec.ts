/**
 * P9-04 — KPI strip interactive filters + counts (doc 9 §14.6; doc 6 §6.1–6.2).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management KPI strip (P9-04)', () => {
	test.setTimeout(180_000);

	test('KPI chips show counts; click sets queue URL and list filter', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const kpiDraft = shell.getByTestId('tm2-kpi-draft');
		await expect(kpiDraft).toBeVisible({ timeout: 60_000 });
		await expect(kpiDraft).toHaveText(/\(\d+\)/);

		await kpiDraft.click();
		await expect(page).toHaveURL(/queue=draft/);
		const filter = shell.getByTestId('tm2-tender-list-filter');
		await expect(filter).toContainText(/Queue|Draft/i);

		await shell.getByTestId('tm2-kpi-published').click();
		await expect(page).toHaveURL(/queue=published/);
		await expect(filter).toContainText(/Published/i);
		await expect(shell.getByTestId('tm2-queue-published')).toHaveClass(/btn-primary/);
	});

	test('deep link ?queue=std-incomplete highlights queue + KPI', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2?queue=std-incomplete`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		await expect(shell.getByTestId('tm2-kpi-std-incomplete')).toHaveClass(/btn-primary/);
		await expect(shell.getByTestId('tm2-queue-std-incomplete')).toHaveClass(/btn-primary/);
		await expect(shell.getByTestId('tm2-tender-list-filter')).toContainText(/STD\s+Incomplete/i);
	});
});
