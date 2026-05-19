/**
 * P9-11 — Timeline tab: deadlines, server time / notice when applicable (doc 9 §17.4).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clickTm2LegacyTab } from '../../helpers/tm2Workbench';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Timeline tab (P9-11)', () => {
	test.setTimeout(180_000);

	test('Timeline tab shows deadline section and warnings area when a tender is selected', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const legacyTab = 'tm2-tab-timeline';
		await expect(shell.getByTestId('tm2-tab-audit')).toBeVisible();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-timeline')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-timeline')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });

		await clickTm2LegacyTab(page, legacyTab);
		await expect(shell.getByTestId('tm2-timeline-key-dates')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-timeline-warnings')).toBeVisible();
		await expect(shell.getByTestId('tm2-timeline-extension-history')).toBeVisible();
		const st = shell.getByTestId('tm2-timeline-server-time');
		const muted = shell.getByTestId('tm2-timeline-server-time-muted');
		await expect(st.or(muted).first()).toBeVisible();
	});
});
