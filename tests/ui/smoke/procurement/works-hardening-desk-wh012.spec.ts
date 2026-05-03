/**
 * Doc 5 §24 — Works Hardening Desk (WH-012).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	clickSaveAndWaitForSavedocs,
	controlInput,
	controlTextScope,
	ensureLinkFieldFromAwesomplete,
} from '../../helpers/deskForm';
import {
	clickStdPocAction,
	clickWorksHardeningAction,
	closeVisibleHtmlModal,
} from '../../helpers/stdAdminConsoleDesk';

const TEMPLATE_CODE = 'KE-PPRA-WORKS-BLDG-2022-04-POC';

const WORKS_HARDENING_LABELS = [
	'Run Works Hardening',
	'Check Works Hardening',
	'View Works Hardening Summary',
	'View Works Snapshot',
] as const;

async function ensureStdTemplateLinked(page: import('@playwright/test').Page) {
	await ensureLinkFieldFromAwesomplete(page, 'std_template', 'PPRA Works', /PPRA Works STD/i);
}

test.describe('WH-012 — Works Hardening Desk buttons', () => {
	test.setTimeout(180_000);

	test('Works Hardening group: four actions, run, summary and snapshot dialogs', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/app/procurement-tender/new?std_template=${encodeURIComponent(TEMPLATE_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		await expect(controlInput(page, 'tender_title')).toBeVisible({ timeout: 120_000 });
		await controlInput(page, 'tender_title').fill('Playwright WH-012 Works Hardening');
		await controlInput(page, 'tender_reference').fill('PW-WH-012');
		await ensureStdTemplateLinked(page);
		await clickSaveAndWaitForSavedocs(page);

		await clickStdPocAction(page, 'Load Sample Tender');
		await expect(
			controlTextScope(page, 'validation_status').getByText('Not Validated', { exact: true }),
		).toBeVisible({ timeout: 120_000 });

		const group = page
			.locator(`.inner-group-button[data-label="${encodeURIComponent('Works Hardening')}"]`)
			.first();
		await expect(group).toBeVisible({ timeout: 120_000 });
		await group.locator('button').first().click();
		for (const label of WORKS_HARDENING_LABELS) {
			await expect(
				group.locator(
					`.dropdown-menu a.dropdown-item[data-label="${encodeURIComponent(label)}"]`,
				),
			).toBeVisible({ timeout: 15_000 });
		}
		await page.keyboard.press('Escape');

		await clickWorksHardeningAction(page, 'Run Works Hardening');

		await expect(controlTextScope(page, 'works_hardening_status')).toHaveText(
			/Warning|Pass|Blocked|Failed|Deferred/,
			{ timeout: 120_000 },
		);

		await clickWorksHardeningAction(page, 'View Works Hardening Summary');
		const summaryModal = page.locator('.modal-dialog:visible').first();
		await expect(summaryModal.getByRole('heading', { name: 'Works Hardening — Summary' })).toBeVisible({
			timeout: 120_000,
		});
		await expect(summaryModal.getByText('6. Snapshot hash', { exact: false })).toBeVisible();
		await closeVisibleHtmlModal(page);

		await clickWorksHardeningAction(page, 'View Works Snapshot');
		const snapModal = page.locator('.modal-dialog:visible').first();
		await expect(snapModal.getByRole('heading', { name: 'Works Hardening — Snapshot' })).toBeVisible({
			timeout: 120_000,
		});
		await expect(
			snapModal.getByText('WORKS_TENDER_STAGE_BASELINE', { exact: false }),
		).toBeVisible({ timeout: 30_000 });
		await closeVisibleHtmlModal(page);
	});
});
