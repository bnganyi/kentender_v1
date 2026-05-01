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

test.describe('STD-WORKS-POC Step 13 — Tender Pack Preview rendering', () => {
	test.setTimeout(180_000);

	test('STD POC group exposes Generate Tender Pack Preview button', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/app/procurement-tender/new?std_template=${encodeURIComponent(TEMPLATE_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		await expect(controlInput(page, 'tender_title')).toBeVisible({ timeout: 120_000 });
		await controlInput(page, 'tender_title').fill('Playwright STD POC Step 13 Buttons');
		await controlInput(page, 'tender_reference').fill('PW-STD-POC-STEP13-BTN');
		await ensureStdTemplateLinked(page);
		await clickSaveAndWaitForSavedocs(page);

		const group = await openStdPocMenu(page);
		await expect(
			group.locator(
				`.dropdown-menu a.dropdown-item[data-label="${encodeURIComponent(
					'Generate Tender Pack Preview',
				)}"]`,
			),
		).toBeVisible();
	});

	test('Generate Tender Pack Preview persists status and HTML on the tender', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(
			`/app/procurement-tender/new?std_template=${encodeURIComponent(TEMPLATE_CODE)}`,
			{ waitUntil: 'domcontentloaded' },
		);

		await expect(controlInput(page, 'tender_title')).toBeVisible({ timeout: 120_000 });
		await controlInput(page, 'tender_title').fill('Playwright STD POC Step 13 Render');
		await controlInput(page, 'tender_reference').fill('PW-STD-POC-STEP13-REN');
		await ensureStdTemplateLinked(page);
		await clickSaveAndWaitForSavedocs(page);

		// Populate the tender so validation can pass and rendering can proceed.
		const sampleTenderResp = waitForControllerCall(page, 'load_sample_tender');
		await clickStdPocAction(page, 'Load Sample Tender');
		await sampleTenderResp;

		const generatePreviewResp = waitForControllerCall(page, 'generate_tender_pack_preview');
		await clickStdPocAction(page, 'Generate Tender Pack Preview');
		const response = await generatePreviewResp;
		const payload = await response.json();
		expect(payload?.message?.ok).toBeTruthy();
		expect(payload?.message?.validation_status).toBe('Passed');
		expect(payload?.message?.required_form_count).toBeGreaterThan(0);

		// `tender_status` is an editable Select — assert via `<select>` value (avoids the
		// strict-mode collision with the sibling read-only `<div class="control-value">`).
		await expect(
			page.locator('.frappe-control[data-fieldname="tender_status"] select'),
		).toHaveValue('Tender Pack Generated', { timeout: 120_000 });

		// `validation_status` is `read_only: 1` in the DocType JSON, so Frappe renders only
		// `<div class="control-value">` (no `<select>`). Scope the text assertion to it.
		await expect(
			page
				.locator('.frappe-control[data-fieldname="validation_status"] .control-value')
				.first(),
		).toHaveText('Passed', { timeout: 120_000 });

		// `generated_tender_pack_html` is `read_only: 1` Long Text — Desk does not render
		// a `<textarea>` for it. Fetch the persisted value via Frappe client RPC instead;
		// detailed HTML assertions live in the focused Python test module.
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
		expect(html).toContain('Tender Pack Preview');
		expect(html).not.toContain('<script');
		expect(html).not.toContain('wkhtmltopdf');
	});
});
