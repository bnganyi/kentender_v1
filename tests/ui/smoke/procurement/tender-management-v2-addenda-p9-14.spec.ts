/**
 * P9-14 — Addenda tab: read-only notice, list, detail cards with output transitions (doc 9 §17.7, doc 6 §20.5 / Q-03).
 * Canonical doc 9 §21.3 Q-03: ``tests/ui/tm2_addenda.spec.ts``.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { clickTm2LegacyTab } from '../../helpers/tm2Workbench';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench Addenda tab (P9-14)', () => {
	test.setTimeout(180_000);

	test('Addenda tab shows notice, list, and detail cards when a tender is selected', async ({
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

		const legacyTab = 'tm2-tab-addenda';
		await expect(shell.getByTestId('tm2-tab-live-tender')).toBeVisible();

		const rows = shell.getByTestId('tm2-tender-list-rows');
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		if (await empty.isVisible().catch(() => false)) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-addenda')).toBeVisible();
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			await clickTm2LegacyTab(page, legacyTab);
			await expect(shell.getByTestId('tm2-tab-panel-addenda')).toBeVisible();
			return;
		}

		await row.click();
		await expect(shell.getByTestId('tm2-detail-sticky')).toBeVisible({ timeout: 60_000 });

		await clickTm2LegacyTab(page, legacyTab);
		await expect(shell.getByTestId('tm2-ad-readonly-notice')).toBeVisible({ timeout: 30_000 });
		await expect(shell.getByTestId('tm2-ad-status-chips')).toBeVisible();
		await expect(shell.getByTestId('tm2-ad-list-wrap')).toBeVisible();
		await expect(shell.getByTestId('tm2-ad-detail-cards')).toBeVisible();

		const bundleTransition = shell.getByTestId('tm2-ad-transition-bundle');
		if ((await bundleTransition.count()) > 0) {
			await expect(bundleTransition.first()).toContainText('→');
		}
	});
});
