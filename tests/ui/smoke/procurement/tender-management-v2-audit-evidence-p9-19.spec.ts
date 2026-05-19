/**
 * P9-19 — Audit & Evidence tab: lifecycle + export entry (doc 9 §17.12, doc 6 §25).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clickTm2LegacyTab } from '../../helpers/tm2Workbench';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Audit & Evidence tab (P9-19)', () => {
	test.setTimeout(180_000);

	test('Audit & Evidence tab shows lifecycle area and export control', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		const legacyTab = 'tm2-tab-audit-evidence';
		await expect(shell.getByTestId('tm2-tab-audit')).toBeVisible();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-audit-evidence')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-audit-evidence')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });

		await clickTm2LegacyTab(page, legacyTab);
		await expect(shell.getByTestId('tm2-ae-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-ae-export-notice')).toBeVisible();
		await expect(shell.getByTestId('tm2-ae-readonly-notice')).not.toContainText(/TM2|workbench|doc 9/i);
		await expect(shell.getByTestId('tm2-ae-export-notice')).not.toContainText(/doc 9|§/i);
		await expect(shell.getByTestId('tm2-timeline-key-dates')).not.toContainText(/TM2/i);
		await expect(shell.getByText('Denied / sensitive actions')).toHaveCount(0);
		await expect(shell.getByTestId('tm2-ae-sensitive-wrap')).toBeVisible();
		await expect(shell.getByTestId('tm2-ae-sensitive-wrap').getByText('Blocked actions', { exact: true })).toBeVisible();
		await expect(shell.getByTestId('tm2-action-more-nav-technical-references')).toHaveCount(0);
		await expect(shell.getByTestId('tm2-open-technical-references')).toBeVisible();
		const lifecycleWrap = shell.getByTestId('tm2-ae-lifecycle-wrap');
		await expect(lifecycleWrap).toBeVisible();
		await expect(lifecycleWrap).not.toContainText(/STD Bound|STD Instance|TM2 Tender/i);
		await expect(shell.getByTestId('tm2-ae-sensitive-wrap')).toBeVisible();
		await expect(shell.getByTestId('tm2-ae-action-export')).toBeVisible();
	});
});
