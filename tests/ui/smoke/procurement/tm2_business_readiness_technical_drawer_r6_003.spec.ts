/**
 * R6-003 / LV-R6-003-01 — TM2 readiness: Bundle/DSM/DOM/DEM/DCM live in the collapsed
 * technical drawer (`plc-br-technical-collapsed` / `plc-technical-evidence-body`) until expanded.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('TM2 business readiness technical drawer (R6-003)', () => {
	test.setTimeout(180_000);

	test('PLC-R6-003-01: STD output lines hidden until drawer opens', async ({ page, baseURL }) => {
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
		const br = panel.getByTestId('plc-business-readiness-summary');
		await expect(br).toBeVisible({ timeout: 90_000 });

		const body = br.getByTestId('plc-technical-evidence-body');

		await expect(body).not.toBeVisible();

		await br.getByTestId('plc-br-technical-summary').click({ timeout: 15_000 });
		await expect(br.locator('details.plc-tm2-readiness-technical-drawer')).toHaveAttribute('open');

		await expect(body).toBeVisible({ timeout: 15_000 });

		const techLines = br.getByTestId('plc-br-technical-line');
		const lineCount = await techLines.count();
		if (lineCount > 0) {
			await expect(techLines.first().locator('.plc-technical-output-code')).toBeVisible();
		} else {
			await expect(br.getByTestId('plc-br-no-tech')).toBeVisible();
		}
	});
});
