/**
 * P9-08 — Tender detail header, state cards, action bar, publish modal shell (doc 9 §16).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management workbench detail (P9-08)', () => {
	test.setTimeout(180_000);

	test('row click loads detail header and state cards; publish modal testid when enabled', async ({
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

		const rows = shell.getByTestId('tm2-tender-list-rows');
		await expect(rows).toBeVisible({ timeout: 60_000 });
		const row = rows.getByTestId('tm2-tender-list-row').first();
		const empty = rows.getByTestId('tm2-tender-list-empty');
		const header = shell.getByTestId('tm2-tender-detail-header');
		await expect(header).toBeVisible();
		if (await empty.isVisible().catch(() => false)) {
			const t = (await header.innerText()).trim();
			expect(t.length).toBeGreaterThan(2);
			return;
		}
		if (!(await row.isVisible().catch(() => false))) {
			const t = (await header.innerText()).trim();
			expect(t.length).toBeGreaterThan(2);
			return;
		}
		await row.click();

		await expect(shell.getByTestId('tm2-state-card-tender_state')).toBeVisible({ timeout: 60_000 });
		await expect(header.locator('.font-weight-bold').first()).toBeVisible();
		await expect(shell.getByTestId('tm2-action-bar').getByTestId('tm2-action-tnd2-view')).toBeVisible();

		const pub = shell.getByTestId('tm2-action-tnd2-publish');
		await expect(pub).toBeVisible();
		if (await pub.isEnabled()) {
			await pub.click();
			await expect(page.getByTestId('tm2-modal-tnd2_publish')).toBeVisible({ timeout: 30_000 });
			await page.keyboard.press('Escape');
		}
	});
});
