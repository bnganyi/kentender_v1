/**
 * P9-18 — Contract Handoff tab: DCM ref + final evaluated price line (doc 9 §17.11, TM2-SMOKE-UI-008).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clickTm2LegacyTab } from '../../helpers/tm2Workbench';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Contract Handoff tab (P9-18)', () => {
	test.setTimeout(180_000);

	test('Contract Handoff tab shows DCM ref and final price row', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const legacyTab = 'tm2-tab-contract-handoff';
		await expect(shell.getByTestId('tm2-tab-handoff')).toBeVisible();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-contract-handoff')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-contract-handoff')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });

		await clickTm2LegacyTab(page, legacyTab);
		await expect(shell.getByTestId('tm2-ch-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-ch-dcm-readonly-notice')).toBeVisible();
		await expect(shell.getByTestId('tm2-ch-dcm-ref')).toBeVisible();
		await expect(shell.getByTestId('tm2-ch-final-price')).toBeVisible();
	});
});
