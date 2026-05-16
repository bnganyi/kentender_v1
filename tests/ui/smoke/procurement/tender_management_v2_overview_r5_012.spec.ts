/**
 * R5-012 — TM2 workbench Overview: next step first + technical refs collapsed by default.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('TM2 Overview next-action-first + technical refs (R5-012)', () => {
	test.setTimeout(180_000);

	test('PLC-R5-012-01: next step precedes summaries; outputs live under collapsed details', async ({
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

		const row = shell.getByTestId('tm2-tender-list-row').first();
		const empty = shell.getByTestId('tm2-tender-list-empty');
		test.skip(
			await empty.isVisible().catch(() => false),
			'No tenders in TM2 queue on this site — cannot exercise Overview.',
		);
		test.skip(!(await row.isVisible().catch(() => false)), 'No selectable tender rows.');

		await row.click();
		await shell.getByTestId('tm2-tab-overview').click({ timeout: 30_000 });

		const panel = shell.getByTestId('tm2-tab-panel-overview');
		await expect(panel.getByTestId('tm2-overview-next-step')).toBeVisible({
			timeout: 60_000,
		});
		await expect(panel.getByTestId('tm2-overview-tender-summary')).toBeVisible();

		await expect(panel.locator(':scope > *').first()).toHaveAttribute(
			'data-testid',
			'tm2-overview-next-step',
		);

		const details = panel.getByTestId('tm2-overview-technical-collapsed');
		await expect(details).toBeVisible();
		await expect(details).not.toHaveAttribute('open');
		await expect(panel.getByTestId('tm2-overview-output-refs')).not.toBeVisible();

		await shell.getByTestId('tm2-overview-technical-summary').click({ timeout: 15_000 });
		await expect(details).toHaveAttribute('open');
		await expect(panel.getByTestId('tm2-overview-output-refs')).toBeVisible({
			timeout: 15_000,
		});
	});
});
