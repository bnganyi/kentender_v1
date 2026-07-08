import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	childTableDataRows,
	clickSaveAndWaitForSavedocs,
	controlInput,
	controlTextScope,
	ensureLinkFieldFromAwesomplete,
} from '../../helpers/deskForm';

const TEMPLATE_CODE = 'KE-PPRA-WORKS-BLDG-2022-04-POC';

const STD_POC_LABELS = [
	'Load Template Defaults',
	'Load Sample Tender',
	'Load Sample Variant',
	'Validate Configuration',
	'Generate Required Forms',
	'Generate Sample BoQ',
	'Prepare Render Context',
] as const;

async function ensureStdTemplateLinked(page: import('@playwright/test').Page) {
	await ensureLinkFieldFromAwesomplete(page, 'std_template', 'PPRA Works', /PPRA Works STD/i);
}

async function openStdPocMenu(page: import('@playwright/test').Page) {
	const groupSelector = `.inner-group-button[data-label="${encodeURIComponent('STD POC')}"]`;
	const group = page.locator(groupSelector).first();
	await expect(group).toBeVisible({ timeout: 60_000 });
	await group.locator('button').first().click();
	return group;
}

async function clickStdPocAction(page: import('@playwright/test').Page, label: string) {
	const group = await openStdPocMenu(page);
	await group.locator(`.dropdown-menu a.dropdown-item[data-label="${encodeURIComponent(label)}"]`).click();
}

test.describe('STD-WORKS-POC Step 12 — Procurement Tender STD POC buttons', () => {
	test.setTimeout(120_000);
	test('STD POC button group on saved Procurement Tender', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/app/procurement-tender/new?std_template=${encodeURIComponent(TEMPLATE_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		await expect(controlInput(page, 'tender_title')).toBeVisible({ timeout: 120_000 });
		await controlInput(page, 'tender_title').fill('Playwright STD POC Tender');
		await controlInput(page, 'tender_reference').fill('PW-STD-POC-STEP12');
		await ensureStdTemplateLinked(page);
		await clickSaveAndWaitForSavedocs(page);

		const group = await openStdPocMenu(page);
		for (const label of STD_POC_LABELS) {
			await expect(
				group.locator(`.dropdown-menu a.dropdown-item[data-label="${encodeURIComponent(label)}"]`),
			).toBeVisible();
		}
	});

	test('STD POC: Load Sample Tender populates lots and BoQ', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/app/procurement-tender/new?std_template=${encodeURIComponent(TEMPLATE_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		await expect(controlInput(page, 'tender_title')).toBeVisible({ timeout: 120_000 });
		await controlInput(page, 'tender_title').fill('Playwright STD POC Load Sample');
		await controlInput(page, 'tender_reference').fill('PW-STD-POC-LOAD-SAMPLE');
		await ensureStdTemplateLinked(page);
		await clickSaveAndWaitForSavedocs(page);

		await clickStdPocAction(page, 'Load Sample Tender');

		await expect(
			controlTextScope(page, 'validation_status').getByText('Not Validated', { exact: true }),
		).toBeVisible({
			timeout: 120_000,
		});

		const lotsRows = childTableDataRows(page, 'lots');
		await expect(lotsRows).toHaveCount(2, { timeout: 120_000 });
		await expect(lotsRows.filter({ hasText: 'LOT-001' })).toHaveCount(1);
		await expect(lotsRows.filter({ hasText: 'LOT-002' })).toHaveCount(1);

		await expect(childTableDataRows(page, 'boq_items')).toHaveCount(9, { timeout: 120_000 });
	});
});
