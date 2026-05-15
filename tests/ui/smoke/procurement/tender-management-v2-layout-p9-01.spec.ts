/**
 * P9-01 — TM2 workbench shell layout A–F (doc 9 §14.2, §14.4).
 * P9-02 — §14.3 detail component hooks + doc §17.1 tab selectors (doc 9 §14.3–14.4).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Tender Management v2 layout shell (P9-01)', () => {
	test.setTimeout(180_000);

	test('§14.4 regions visible on /app/tender-management-v2', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.getByTestId('tm2-workbench-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		for (const id of [
			'tm2-page-title',
			'tm2-action-new-tender',
			'tm2-action-my-actions',
			'tm2-action-evidence-export',
			'tm2-kpi-strip',
			'tm2-scope-tabs',
			'tm2-queue-bar',
			'tm2-search-input',
			'tm2-filter-panel',
			'tm2-tender-list',
			'tm2-tender-detail',
			'tm2-action-bar',
			'tm2-blockers-panel',
		]) {
			await expect(shell.getByTestId(id)).toBeVisible({ timeout: 30_000 });
		}

		await expect(shell.getByTestId('tm2-kpi-draft')).toBeVisible();
		await expect(shell.getByTestId('tm2-queue-draft')).toBeVisible();
	});
});

test.describe('Tender Management v2 component tree selectors (P9-02)', () => {
	test.setTimeout(180_000);

	test('§14.3 / §17.1 — scope ids, list row, detail chrome, all tab selectors', async ({
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

		await expect(shell.getByTestId('tm2-scope-tabs').getByTestId('tm2-scope-my-work')).toBeVisible();
		const list = shell.getByTestId('tm2-tender-list');
		await expect(list.getByTestId('tm2-tender-list-rows')).toBeVisible();
		const rows = list.getByTestId('tm2-tender-list-rows');
		await expect(rows.locator('[data-testid="tm2-tender-list-row"], [data-testid="tm2-tender-list-empty"]').first()).toBeVisible();

		const detail = shell.getByTestId('tm2-tender-detail');
		await expect(detail.getByTestId('tm2-tender-detail-header')).toBeVisible();
		await expect(detail.getByTestId('tm2-state-summary-cards')).toBeVisible();
		await expect(detail.getByTestId('tm2-detail-tabs')).toBeVisible();

		const tabIds = [
			'tm2-tab-overview',
			'tm2-tab-std-readiness',
			'tm2-tab-timeline',
			'tm2-tab-supplier-access',
			'tm2-tab-clarifications',
			'tm2-tab-addenda',
			'tm2-tab-submissions',
			'tm2-tab-opening-readiness',
			'tm2-tab-evaluation-handoff',
			'tm2-tab-contract-handoff',
			'tm2-tab-audit-evidence',
		];
		for (const id of tabIds) {
			await expect(detail.getByTestId(id)).toBeVisible({ timeout: 30_000 });
		}
	});
});
