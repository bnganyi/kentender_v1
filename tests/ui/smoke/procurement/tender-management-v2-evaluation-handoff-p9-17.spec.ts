/**
 * P9-17 — Evaluation Handoff tab: DEM ref + criteria notice (doc 9 §17.10, doc 6 §23).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clickTm2LegacyTab } from '../../helpers/tm2Workbench';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Evaluation Handoff tab (P9-17)', () => {
	test.setTimeout(180_000);

	test('Evaluation Handoff tab shows evaluation rules ref under technical references', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const legacyTab = 'tm2-tab-evaluation-handoff';
		await expect(shell.getByTestId('tm2-tab-handoff')).toBeVisible();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-evaluation-handoff')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-evaluation-handoff')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });

		await clickTm2LegacyTab(page, legacyTab);
		await expect(shell.getByTestId('tm2-eh-readonly-notice')).toBeVisible({ timeout: 30_000 });
		const techRefs = shell.getByTestId('tm2-eh-technical-refs');
		await expect(techRefs).toBeVisible();
		await techRefs.locator('summary').click();
		await expect(shell.getByTestId('tm2-eh-dem-ref')).toBeVisible();
		await expect(shell.getByTestId('tm2-eh-criteria-notice')).toBeVisible();
		await expect(shell.getByTestId('tm2-eh-criteria-notice')).toContainText(/cannot be modified/i);
	});
});
