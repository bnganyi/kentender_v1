/**
 * R6-001 / LV-R6-001-01 — TM2 workbench Overview: `plc-business-readiness-summary`
 * shows business labels first; STD output codes under collapsed technical block.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('TM2 Business readiness summary (R6-001)', () => {
	test.setTimeout(180_000);

	test('PLC-R6-001-01: business labels visible; technical codes collapsed by default', async ({
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
		const br = panel.getByTestId('plc-business-readiness-summary');
		await expect(br).toBeVisible({ timeout: 90_000 });

		await expect(br.getByTestId('plc-br-business-label').first()).toContainText(
			'Tender document package ready',
			{ timeout: 15_000 },
		);

		const techDetails = br.getByTestId('plc-br-technical-collapsed');
		await expect(techDetails).toBeVisible();
		await expect(techDetails).not.toHaveAttribute('open');

		const overviewTech = panel.getByTestId('tm2-overview-technical-collapsed');
		await expect(overviewTech).toBeVisible();
		await expect(overviewTech).not.toHaveAttribute('open');
	});
});
