/**
 * STD-CFG — Playwright data-bound assertions against UI fixture template.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const FIXTURE_CODE = 'STD-CFG-UI-FIXTURE';

test.describe('STD Config UI — fixture data binding', () => {
	test.setTimeout(180_000);

	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('configurator overview shows seeded metadata title', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/overview`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-overview"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-identity-card"]')).toBeVisible({
			timeout: 30_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-identity-form"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-progress-card"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-applies-to-preview"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-applies-copy"]')).toBeVisible();
		const titleInput = page.locator('[data-kt-std-field="title"]');
		await expect(titleInput).toHaveValue(/Building Works/i);
		await expect(page.locator('[data-kt-std-field="version_label"]')).toHaveValue('2.1');
		await expect(page.locator('.kt-std-cfg-applies-list li')).toHaveCount(6);
	});

	test('configurator applicability tab matches mockup regions and fixture data', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/applicability`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-applicability"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-applicability-banner"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-applicability-banner-title"]')).toHaveText(
			/Applicability Rules/i,
		);
		await expect(page.locator('[data-testid="kt-std-cfg-applicability-banner"]')).toContainText(
			/KES above 6,000,000/i,
		);
		await expect(page.locator('[data-testid="kt-std-cfg-conflict-check"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-test-section"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-classification"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-entity-funding"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-financial-limits"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-financial-limits-card"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-applicability-applies-preview"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-entity-scope-pills"]')).toBeVisible();
		await expect(page.locator('.kt-std-cfg-funding-cards')).toBeVisible();
		await expect(page.locator('[data-kt-std-field="works_subtype"]')).toHaveValue(/Building Works/i);
		await expect(page.locator('[data-testid="kt-std-cfg-test-section"]')).toHaveClass(/kt-std-cfg-test-section/);
		await expect(page.locator('.kt-std-cfg-applies-panel__list li')).toHaveCount(6);

		const stackMetrics = await page.evaluate(() => {
			const section = document.querySelector('[data-testid="kt-std-cfg-applicability"]');
			const banner = document.querySelector('[data-testid="kt-std-cfg-applicability-banner"]');
			const conflict = document.querySelector('[data-testid="kt-std-cfg-conflict-check"]');
			const testSection = document.querySelector('[data-testid="kt-std-cfg-test-section"]');
			if (!section || !banner || !conflict || !testSection) {
				return { ok: false };
			}
			const stackStyle = getComputedStyle(section);
			const gapPx = parseFloat(stackStyle.gap || stackStyle.rowGap || '0');
			const bannerToConflict =
				conflict.getBoundingClientRect().top - banner.getBoundingClientRect().bottom;
			const conflictToTest =
				testSection.getBoundingClientRect().top - conflict.getBoundingClientRect().bottom;
			return {
				ok: true,
				hasTabStack: section.classList.contains('kt-std-cfg-tab-stack'),
				gapPx,
				bannerToConflict,
				conflictToTest,
			};
		});
		expect(stackMetrics.ok).toBe(true);
		expect(stackMetrics.hasTabStack).toBe(true);
		expect(stackMetrics.gapPx).toBeGreaterThanOrEqual(20);
		expect(stackMetrics.bannerToConflict).toBeGreaterThanOrEqual(20);
		expect(stackMetrics.conflictToTest).toBeGreaterThanOrEqual(20);
	});

	test('configurator tender fields tab matches mockup matrix and fixture data', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/tender-fields`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-tender-fields"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-tender-fields"]')).toHaveClass(/kt-std-cfg-tab-stack/);
		await expect(page.locator('[data-testid="kt-std-cfg-tf-actions"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-tender-fields-matrix"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-tf-guidance"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-tf-group-tender_identity"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-tf-group-timetable"]')).toBeVisible();
		await expect(page.locator('.kt-std-cfg-tf-table thead th')).toHaveCount(7);
		await expect(page.locator('[data-testid="kt-std-cfg-tf-field-row"]')).toHaveCount(3);
		await expect(page.locator('[data-testid="kt-std-cfg-tender-fields-matrix"]')).toContainText(/Tender Title/i);
		await expect(page.locator('[data-testid="kt-std-cfg-tender-fields-matrix"]')).toContainText(
			/Submission Deadline/i,
		);

		const layoutMetrics = await page.evaluate(() => {
			const section = document.querySelector('[data-testid="kt-std-cfg-tender-fields"]');
			const matrix = document.querySelector('[data-testid="kt-std-cfg-tender-fields-matrix"]');
			const guidance = document.querySelector('[data-testid="kt-std-cfg-tf-guidance"]');
			if (!section || !matrix || !guidance) return { ok: false };
			const layout = section.querySelector('.kt-std-cfg-tf-layout');
			const layoutGap = layout ? parseFloat(getComputedStyle(layout).gap || '0') : 0;
			const matrixToGuidance = guidance.getBoundingClientRect().top - matrix.getBoundingClientRect().bottom;
			return { ok: true, layoutGap, matrixToGuidance };
		});
		expect(layoutMetrics.ok).toBe(true);
		expect(layoutMetrics.layoutGap).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.matrixToGuidance).toBeGreaterThanOrEqual(20);
	});

	test('configurator supplier requirements tab matches pack matrix and fixture data', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/supplier-requirements`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-supplier-requirements"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-supplier-requirements"]')).toHaveClass(/kt-std-cfg-tab-stack/);
		await expect(page.locator('[data-testid="kt-std-cfg-sr-actions"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-supplier-requirements-matrix"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-sr-guidance"]')).toBeVisible();
		await expect(page.locator('.kt-std-cfg-sr-table thead th')).toHaveCount(7);
		await expect(page.locator('[data-testid="kt-std-cfg-sr-row"]')).toHaveCount(3);
		await expect(page.locator('[data-testid="kt-std-cfg-supplier-requirements-matrix"]')).toContainText(
			/Form of Tender/i,
		);
		await expect(page.locator('[data-testid="kt-std-cfg-supplier-requirements-matrix"]')).toContainText(
			/Tax Compliance Certificate/i,
		);

		const layoutMetrics = await page.evaluate(() => {
			const section = document.querySelector('[data-testid="kt-std-cfg-supplier-requirements"]');
			const matrix = document.querySelector('[data-testid="kt-std-cfg-supplier-requirements-matrix"]');
			const guidance = document.querySelector('[data-testid="kt-std-cfg-sr-guidance"]');
			if (!section || !matrix || !guidance) return { ok: false };
			const layout = section.querySelector('.kt-std-cfg-sr-layout');
			const layoutGap = layout ? parseFloat(getComputedStyle(layout).gap || '0') : 0;
			const matrixToGuidance = guidance.getBoundingClientRect().top - matrix.getBoundingClientRect().bottom;
			return { ok: true, layoutGap, matrixToGuidance };
		});
		expect(layoutMetrics.ok).toBe(true);
		expect(layoutMetrics.layoutGap).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.matrixToGuidance).toBeGreaterThanOrEqual(20);
	});

	test('configurator forms and attachments tab matches mockup layout and fixture data', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/forms-attachments`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-forms-attachments"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-forms"]')).toHaveClass(/kt-std-cfg-tab-stack/);
		await expect(page.locator('[data-testid="kt-std-cfg-forms-documents"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-forms-supplier-forms"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-fa-info-row"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-forms-warn"]')).toBeVisible();
		await expect(page.locator('.kt-std-cfg-fa-table thead th')).toHaveCount(9);
		await expect(page.locator('[data-testid="kt-std-cfg-fa-doc-row"]')).toHaveCount(3);
		await expect(page.locator('[data-testid="kt-std-cfg-fa-supplier-card"]')).toHaveCount(2);
		await expect(page.locator('[data-testid="kt-std-cfg-forms-documents"]')).toContainText(
			/Standard Tender Document/i,
		);
		await expect(page.locator('[data-testid="kt-std-cfg-forms-documents"]')).toContainText(
			/Bill of Quantities Template/i,
		);
		await expect(page.locator('[data-testid="kt-std-cfg-forms-supplier-forms"]')).toContainText(/Company Profile/i);
		await expect(page.locator('[data-testid="kt-std-cfg-forms-warn"]')).toContainText(/Form of Agreement/i);

		const layoutMetrics = await page.evaluate(() => {
			const section = document.querySelector('[data-testid="kt-std-cfg-forms"]');
			const documents = document.querySelector('[data-testid="kt-std-cfg-forms-documents"]');
			const supplierForms = document.querySelector('[data-testid="kt-std-cfg-forms-supplier-forms"]');
			const info = document.querySelector('[data-testid="kt-std-cfg-fa-info-row"]');
			if (!section || !documents || !supplierForms || !info) return { ok: false };
			const layout = section.querySelector('.kt-std-cfg-fa-layout');
			const layoutGap = layout ? parseFloat(getComputedStyle(layout).gap || '0') : 0;
			const documentsToSupplier =
				supplierForms.getBoundingClientRect().top - documents.getBoundingClientRect().bottom;
			const supplierToInfo = info.getBoundingClientRect().top - supplierForms.getBoundingClientRect().bottom;
			return { ok: true, layoutGap, documentsToSupplier, supplierToInfo };
		});
		expect(layoutMetrics.ok).toBe(true);
		expect(layoutMetrics.layoutGap).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.documentsToSupplier).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.supplierToInfo).toBeGreaterThanOrEqual(20);
	});

	test('configurator evaluation setup tab matches mockup bento and fixture stages', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/evaluation-setup`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-evaluation-setup"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-evaluation"]')).toHaveClass(/kt-std-cfg-tab-stack/);
		await expect(page.locator('[data-testid="kt-std-cfg-ev-basis"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ev-bento"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ev-conflict"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ev-ready"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ev-stages"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ev-stage-card"]')).toHaveCount(4);
		await expect(page.locator('[data-testid="kt-std-cfg-ev-bento"]')).toContainText(/04/);
		await expect(page.locator('[data-testid="kt-std-cfg-ev-stages"]')).toContainText(/Preliminary Evaluation/i);
		await expect(page.locator('[data-testid="kt-std-cfg-ev-stages"]')).toContainText(/Technical Evaluation/i);
		await expect(page.locator('[data-testid="kt-std-cfg-ev-conflict"]')).toContainText(/KES/i);

		const layoutMetrics = await page.evaluate(() => {
			const section = document.querySelector('[data-testid="kt-std-cfg-evaluation"]');
			const basis = document.querySelector('[data-testid="kt-std-cfg-ev-basis"]');
			const bento = document.querySelector('[data-testid="kt-std-cfg-ev-bento"]');
			const stages = document.querySelector('[data-testid="kt-std-cfg-ev-stages"]');
			if (!section || !basis || !bento || !stages) return { ok: false };
			const layout = section.querySelector('.kt-std-cfg-ev-layout');
			const layoutGap = layout ? parseFloat(getComputedStyle(layout).gap || '0') : 0;
			const basisToBento = bento.getBoundingClientRect().top - basis.getBoundingClientRect().bottom;
			const bentoToStages = stages.getBoundingClientRect().top - bento.getBoundingClientRect().bottom;
			return { ok: true, layoutGap, basisToBento, bentoToStages };
		});
		expect(layoutMetrics.ok).toBe(true);
		expect(layoutMetrics.layoutGap).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.basisToBento).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.bentoToStages).toBeGreaterThanOrEqual(20);
	});

	test('configurator contract terms tab matches mockup matrix and fixture data', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/contract-terms`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-tab-panel-contract-terms"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="kt-std-cfg-contract-terms"]')).toHaveClass(/kt-std-cfg-tab-stack/);
		await expect(page.locator('[data-testid="kt-std-cfg-ct-governing"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ct-matrix"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ct-readiness"]')).toBeVisible();
		await expect(page.locator('[data-testid="kt-std-cfg-ct-issues"]')).toBeVisible();
		await expect(page.locator('.kt-std-cfg-ct-table thead th')).toHaveCount(10);
		await expect(page.locator('[data-testid="kt-std-cfg-ct-term-row"]')).toHaveCount(6);
		await expect(page.locator('[data-testid="kt-std-cfg-ct-matrix"]')).toContainText(/Performance Security/i);
		await expect(page.locator('[data-testid="kt-std-cfg-ct-matrix"]')).toContainText(/Liquidated Damages/i);
		await expect(page.locator('[data-testid="kt-std-cfg-ct-issues"]')).toContainText(/2 issues/i);

		const layoutMetrics = await page.evaluate(() => {
			const section = document.querySelector('[data-testid="kt-std-cfg-contract-terms"]');
			const governing = document.querySelector('[data-testid="kt-std-cfg-ct-governing"]');
			const matrix = document.querySelector('[data-testid="kt-std-cfg-ct-matrix"]');
			const readiness = document.querySelector('[data-testid="kt-std-cfg-ct-readiness"]');
			if (!section || !governing || !matrix || !readiness) return { ok: false };
			const layout = section.querySelector('.kt-std-cfg-ct-layout');
			const layoutGap = layout ? parseFloat(getComputedStyle(layout).gap || '0') : 0;
			const governingToMatrix = matrix.getBoundingClientRect().top - governing.getBoundingClientRect().bottom;
			const matrixToReadiness = readiness.getBoundingClientRect().top - matrix.getBoundingClientRect().bottom;
			return { ok: true, layoutGap, governingToMatrix, matrixToReadiness };
		});
		expect(layoutMetrics.ok).toBe(true);
		expect(layoutMetrics.layoutGap).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.governingToMatrix).toBeGreaterThanOrEqual(20);
		expect(layoutMetrics.matrixToReadiness).toBeGreaterThanOrEqual(20);
	});

	test('harmonized auxiliary tabs render tab-stack panels', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const tabChecks: Array<{ slug: string; panel: string; extra?: string }> = [
			{ slug: 'rules-validations', panel: '[data-testid="kt-std-cfg-rv-rules"]' },
			{ slug: 'preview', panel: '[data-testid="kt-std-cfg-preview-modes"]', extra: '[data-testid="kt-std-cfg-preview-body"]' },
			{ slug: 'approval', panel: '[data-testid="kt-std-cfg-approval-summary"]', extra: '[data-testid="kt-std-cfg-approval-governance"]' },
			{ slug: 'evidence', panel: '[data-testid="kt-std-cfg-evidence-inventory"]', extra: '[data-testid="kt-std-cfg-table-evidence"]' },
			{ slug: 'technical-json', panel: '[data-testid="kt-std-cfg-technical-json-panel"]', extra: '[data-testid="kt-std-cfg-technical-json-body"]' },
		];
		for (const tab of tabChecks) {
			await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/${tab.slug}`);
			await page.waitForLoadState('domcontentloaded');
			await dismissOptionalDeskModals(page);
			await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
			await expect(page.locator(`[data-testid="kt-std-cfg-tab-panel-${tab.slug}"]`)).toBeVisible({
				timeout: 90_000,
			});
			const stack = page.locator(`[data-testid="kt-std-cfg-${tab.slug === 'rules-validations' ? 'rules' : tab.slug}"]`);
			await expect(stack).toHaveClass(/kt-std-cfg-tab-stack/);
			await expect(page.locator(tab.panel)).toBeVisible();
			if (tab.extra) {
				await expect(page.locator(tab.extra)).toBeVisible();
			}
			await expect(page.locator('[data-testid="kt-std-cfg-footer-actions"]')).toBeVisible();
		}
	});

	test('v2 library exposes advanced catalogue disclosure for administrator', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="std-library-advanced-view-toggle"]')).toBeVisible();
		await page.locator('[data-testid="std-library-advanced-view-toggle"]').click();
		await page.locator('[data-testid="std-library-advanced-catalogue-open"]').click();
		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="std-library-list"]')).toBeVisible();
	});

	test('technical-json tab exposes editable editor for administrator on fixture', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-configurator/${FIXTURE_CODE}/technical-json`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-cfg-root"]')).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="kt-std-cfg-technical-json-toolbar"]')).toBeVisible({
			timeout: 30_000,
		});
		const editor = page.locator('[data-kt-std-technical-json-editor]');
		await expect(editor).toBeVisible();
		const original = await editor.inputValue();
		const parsed = JSON.parse(original) as { std_config?: { metadata?: { title?: string } } };
		const pristineTitle = parsed.std_config?.metadata?.title || '';
		const marker = `pw-tech-json-${Date.now()}`;
		const markerTitle = `${pristineTitle} (${marker})`;
		parsed.std_config = parsed.std_config || {};
		parsed.std_config.metadata = parsed.std_config.metadata || {};
		parsed.std_config.metadata.title = markerTitle;
		const modified = JSON.stringify(parsed, null, 2);

		const waitForTechnicalJsonSave = () =>
			page.waitForResponse(
				(response) =>
					response.url().includes('save_std_configurator_technical_json') && response.status() === 200,
				{ timeout: 30_000 },
			);

		await editor.fill(modified);
		const firstSave = waitForTechnicalJsonSave();
		await page.locator('[data-kt-std-technical-json-save]').click();
		await firstSave;
		await expect(editor).toHaveValue(new RegExp(marker), { timeout: 15_000 });

		parsed.std_config.metadata.title = pristineTitle;
		await editor.fill(JSON.stringify(parsed, null, 2));
		const secondSave = waitForTechnicalJsonSave();
		await page.locator('[data-kt-std-technical-json-save]').click();
		await secondSave;
		await expect(editor).not.toHaveValue(new RegExp(marker), { timeout: 15_000 });
	});

	test('library row shows status pill with dot for fixture template', async ({ page, baseURL }) => {
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="kt-std-lib-root"]')).toBeVisible({ timeout: 90_000 });
		const fixtureRow = page.locator(`[data-template-code="${FIXTURE_CODE}"]`);
		if ((await fixtureRow.count()) === 0) {
			test.skip(true, 'UI fixture template not seeded on site');
		}
		await expect(fixtureRow.locator('[data-testid="kt-std-lib-status-pill"] .kt-std-status-pill__dot')).toBeVisible();
		await expect(fixtureRow.locator('[data-testid="kt-std-lib-row-method"]')).not.toBeEmpty();
	});
});
