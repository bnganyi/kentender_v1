/**
 * P9-05 — Queue bar §14.7: all `tm2-queue-*` chips with counts; `tm2-queue-std-incomplete` present (doc 9 §14.7; doc 7 §28.2).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const QUEUE_TEST_IDS = [
	'tm2-queue-draft',
	'tm2-queue-std-incomplete',
	'tm2-queue-ready-review',
	'tm2-queue-returned',
	'tm2-queue-approved',
	'tm2-queue-published',
	'tm2-queue-clarifications',
	'tm2-queue-addenda',
	'tm2-queue-closing-soon',
	'tm2-queue-closed',
	'tm2-queue-opening-ready',
	'tm2-queue-evaluation-ready',
	'tm2-queue-cancelled',
] as const;

test.describe('Tender Management queue bar (P9-05)', () => {
	test.setTimeout(180_000);

	test('queue bar lists all §14.7 selectors with (count); std-incomplete chip visible', async ({
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

		const bar = shell.getByTestId('tm2-queue-bar');
		await expect(bar).toBeVisible({ timeout: 60_000 });

		for (const id of QUEUE_TEST_IDS) {
			const chip = bar.getByTestId(id);
			await expect(chip).toBeVisible();
			await expect(chip).toHaveText(/\(\d+\)/);
		}

		const stdInc = bar.getByTestId('tm2-queue-std-incomplete');
		await expect(stdInc).toBeVisible();
	});
});
