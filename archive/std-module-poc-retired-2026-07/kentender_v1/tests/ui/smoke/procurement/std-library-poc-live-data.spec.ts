/**
 * Live (unmocked) assertions — WORKS POC package projection renders in Official STD Library shell.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const POC_CODE = 'KE-PPRA-WORKS-BLDG-2022-04-POC';

test.describe('STD Library — WORKS POC live package projection', () => {
	test.setTimeout(180_000);

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('advanced catalogue renders projected sections and raw JSON without manual expand', async ({
		page,
		baseURL,
	}) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const detailResponse = page.waitForResponse(
			(resp) =>
				resp.url().includes('get_std_library_template_detail') &&
				resp.status() === 200,
			{ timeout: 90_000 },
		);
		await page.goto(
			`${root}/app/std-engine-advanced?std_code=${encodeURIComponent(POC_CODE)}&tab=advanced`,
		);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({ timeout: 90_000 });
		await detailResponse;

		await expect(page.locator('.std-library-detail-title')).toContainText(/Building/i, {
			timeout: 30_000,
		});
		await expect(page.locator('[data-testid="std-advanced-technical-view"]')).toBeVisible({
			timeout: 30_000,
		});

		const sectionsTable = page.locator(
			'[data-testid="std-advanced-section-table-sections_clauses"]',
		);
		await expect(sectionsTable).toBeVisible({ timeout: 30_000 });
		await expect(sectionsTable.locator('tbody tr').first()).toBeVisible();
		await expect(sectionsTable).not.toContainText(
			'Shell ready. Detailed internals are implemented in follow-on tickets',
		);

		const rawJson = page.locator('[data-testid="std-advanced-raw-package-json"]');
		await expect(rawJson).toBeVisible({ timeout: 30_000 });
		await expect(rawJson).toContainText(/"manifest"/);
	});

	test('summary tab shows projected title and procurement methods', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine-advanced?std_code=${encodeURIComponent(POC_CODE)}`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="std-library-summary-tab"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator('[data-testid="std-library-summary-identity"]')).toContainText(/Building/i);
		await expect(page.locator('[data-testid="std-library-summary-supported-use"]')).toContainText(
			/Open Competitive Tendering/i,
		);
	});

	test('configurator overview shows projected metadata for WORKS POC', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${POC_CODE}/overview`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-title"]')).toContainText(/Building/i, {
			timeout: 90_000,
		});
		await expect(page.locator('[data-kt-std-field="title"]')).toHaveValue(/Building/i, {
			timeout: 90_000,
		});
	});

	test('configurator tender-fields tab lists imported package fields for WORKS POC', async ({
		page,
		baseURL,
	}) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${POC_CODE}/tender-fields`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-tender-fields"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-kt-std-field-row]').first()).toBeVisible({ timeout: 30_000 });
		await expect(page.locator('[data-kt-std-field-row]')).not.toHaveCount(0);
	});

	test('configurator technical-json tab renders package_json for WORKS POC', async ({
		page,
		baseURL,
	}) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const jsonResponse = page.waitForResponse(
			(resp) =>
				resp.url().includes('get_std_configurator_technical_json') &&
				resp.request().method() === 'POST' &&
				resp.status() === 200,
			{ timeout: 90_000 },
		);
		await page.goto(`${root}/app/std-configurator/${POC_CODE}/technical-json`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await jsonResponse;
		const body = page.locator('[data-testid="kt-std-cfg-technical-json-body"]');
		await expect(body).toBeVisible({ timeout: 90_000 });
		await expect(body).toContainText(/"manifest"/);
		await expect(body).toContainText(/"sections"/);
	});

	test('configurator normalizes undefined tab slug to overview', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${POC_CODE}/undefined`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-overview"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-tab-overview"]')).toHaveClass(/is-active/);
	});
});
