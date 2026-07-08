import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	clickSaveAndWaitForSavedocs,
	controlInput,
	ensureLinkFieldFromAwesomplete,
} from '../../helpers/deskForm';

const TEMPLATE_CODE = 'KE-PPRA-WORKS-BLDG-2022-04-POC';

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

async function waitForControllerCall(
	page: import('@playwright/test').Page,
	method: string,
) {
	return page.waitForResponse(
		(resp) =>
			resp.url().includes(method) &&
			resp.request().method() === 'POST' &&
			resp.status() === 200,
		{ timeout: 120_000 },
	);
}

test.describe('STD-WORKS-POC Step 16 — End-to-end Desk smoke (happy path)', () => {
	test.setTimeout(240_000);

	test('Primary smoke: load sample → validate → required forms → tender-pack preview', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/app/procurement-tender/new?std_template=${encodeURIComponent(TEMPLATE_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		await expect(controlInput(page, 'tender_title')).toBeVisible({ timeout: 120_000 });
		await controlInput(page, 'tender_title').fill('Playwright STD POC Step 16 E2E');
		await controlInput(page, 'tender_reference').fill('PW-STD-POC-STEP16-E2E');
		await ensureStdTemplateLinked(page);
		await clickSaveAndWaitForSavedocs(page);

		const loadSample = waitForControllerCall(page, 'load_sample_tender');
		await clickStdPocAction(page, 'Load Sample Tender');
		await loadSample;

		await expect(controlInput(page, 'tender_title')).toHaveValue(
			/Construction of Ward Administration Block/,
			{ timeout: 120_000 },
		);

		const validateResp = waitForControllerCall(page, 'validate_tender_configuration');
		await clickStdPocAction(page, 'Validate Configuration');
		await validateResp;

		await expect(
			page.locator('.frappe-control[data-fieldname="validation_status"] .control-value').first(),
		).toHaveText('Passed', { timeout: 120_000 });

		const reqForms = waitForControllerCall(page, 'generate_required_forms');
		await clickStdPocAction(page, 'Generate Required Forms');
		await reqForms;

		const previewResp = waitForControllerCall(page, 'generate_tender_pack_preview');
		await clickStdPocAction(page, 'Generate Tender Pack Preview');
		const preview = await previewResp;
		const previewPayload = await preview.json();
		expect(previewPayload?.message?.ok).toBeTruthy();
		expect(previewPayload?.message?.validation_status).toBe('Passed');

		await expect(
			page.locator('.frappe-control[data-fieldname="tender_status"] select'),
		).toHaveValue('Tender Pack Generated', { timeout: 120_000 });

		const docName = page.url().match(/procurement-tender\/([^?#/]+)/)?.[1] ?? '';
		expect(docName).toBeTruthy();
		const fetchResp = await page.request.get(
			`/api/method/frappe.client.get_value?doctype=Procurement+Tender&filters=${encodeURIComponent(
				JSON.stringify({ name: docName }),
			)}&fieldname=${encodeURIComponent(JSON.stringify(['generated_tender_pack_html']))}`,
		);
		expect(fetchResp.ok()).toBeTruthy();
		const fetched = await fetchResp.json();
		const html: string = fetched?.message?.generated_tender_pack_html ?? '';
		expect(html).toContain('POC Preview Only');
		expect(html.toLowerCase()).toContain('representative sample structured data');
		expect(html).toContain(TEMPLATE_CODE);
		expect(html).toContain('Template and Configuration Audit Summary');
		expect(html).toContain('Package Hash');
		expect(html).toContain('Configuration Hash');
		expect(html).not.toContain('<script');
	});
});
