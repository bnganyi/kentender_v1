/**
 * STD-LIB-0610 — Accessibility basics (pack doc 2 §27).
 */
import type { Page } from '@playwright/test';
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const VC_A11Y = 'PPRA-WORKS-A11Y-2022';

async function routeLibraryCore(
	page: Page,
	opts?: { denyImport?: boolean; denyImportMessage?: string; templatesAlwaysFail?: boolean },
) {
	const denyMsg = opts?.denyImportMessage ?? 'Import gated for accessibility test.';
	await page.route('**/api/method/**get_std_library_summary_counts*', async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				message: {
					active_count: 2,
					needs_attention_count: 1,
					ready_for_review_count: 0,
					superseded_count: 0,
					package_import_count: 1,
					bundle_issue_count: 0,
				},
			}),
		});
	});
	/** Action availability + templates + detail (GET path or POST body cmd). */
	await page.route('**/api/method/**', async (route) => {
		const req = route.request();
		const url = req.url();
		const body = req.postData() || '';
		const isActionAvail =
			url.includes('get_std_library_action_availability') ||
			body.includes('get_std_library_action_availability');
		if (isActionAvail) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						actions: [
							{
								action_code: 'IMPORT_OFFICIAL_STD_PACKAGE',
								allowed: opts?.denyImport ? false : true,
								denial_code: opts?.denyImport ? 'TEST_DENY' : null,
								message: opts?.denyImport ? denyMsg : 'Allowed',
								requires_confirmation: false,
								risk_level: 'High',
							},
							{
								action_code: 'REGISTER_SOURCE_DOCUMENT',
								allowed: true,
								denial_code: null,
								message: 'Allowed',
								requires_confirmation: false,
								risk_level: 'High',
							},
							{
								action_code: 'VALIDATE_LIBRARY',
								allowed: true,
								denial_code: null,
								message: 'Allowed',
								requires_confirmation: false,
								risk_level: 'High',
							},
						],
					},
				}),
			});
			return;
		}
		const isDetail =
			url.includes('get_std_library_template_detail') || body.includes('get_std_library_template_detail');
		const isTemplates =
			(url.includes('get_std_library_templates') || body.includes('get_std_library_templates')) &&
			!url.includes('get_std_library_template_detail') &&
			!body.includes('get_std_library_template_detail');
		if (isDetail) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'PPRA Works — DOC1',
							version_code: VC_A11Y,
							revision_label: 'Rev April 2022',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner: 'Active.',
							summary: {
								identity: {
									title: 'PPRA Works',
									revision: 'Rev April 2022',
									authority: 'PPRA',
									template_family: 'WORKS',
								},
								source_evidence: {
									source_document: 'DOC1',
									source_file: 'Registered',
									source_hash: 'SHA256…',
									evidence_status: 'Registered',
								},
								supported_use: {
									category: 'Works',
									methods: ['Open Tender'],
									contract_type: 'Unit Rate',
									requires_boq: 'Yes',
								},
								health_summary: {
									validation: 'Passed',
									bundle_preview: 'Available',
									generated_models: 'Available',
								},
								output_summary: { line: 'Ready.' },
								next_action: { status: 'Active', action: 'Preview bundle.' },
							},
							validation: {
								overall_status: 'Passed',
								severity: 'Low',
								categories: [{ category: 'Structure Integrity', state: 'Passed' }],
								issues: [],
								remediation: 'None.',
							},
							bundle_preview: {
								status_bar: {
									preview_status: 'Available',
									last_generated: '2026-05-08',
									output_type: 'Template-level preview',
									placeholder_count: 2,
									render_warnings: 0,
								},
								outline: ['Invitation to Tender', 'Instructions to Tenderers'],
								preview_blocks: [
									{
										section: 'Invitation to Tender',
										content: 'Invitation preview.',
									},
									{
										section: 'Instructions to Tenderers',
										content: 'ITT preview.',
									},
								],
								placeholders: [],
								actions: {
									generate_preview: { allowed: false, visible: true, message: 'Generate blocked.' },
									download_pdf: { allowed: true, visible: true, message: 'Allowed' },
									download_docx: { allowed: false, visible: true, message: 'DOCX blocked.' },
									view_placeholders: { allowed: true, visible: true, message: 'Allowed' },
								},
							},
							usage: {
								summary: { tenders_using_count: 0 },
								tenders: [],
								instances: [],
								outputs: [],
								addenda: [],
							},
							supersession: {
								lineage: {
									current_version: VC_A11Y,
									supersedes: 'None',
									superseded_by: 'None',
									reason: '—',
									effective_date: '—',
								},
								impact: {
									existing_tender_impact: 'Impact text.',
									new_tenders_impact: 'New tenders.',
								},
								actions: {
									create_new_revision: { allowed: false, message: 'Cannot revise active.' },
								},
							},
							advanced: {
								intro_text: 'Advanced intro copy for screen readers.',
								sections: [
									{ key: 'sections_clauses', label: 'Sections and Clauses' },
									{ key: 'raw_package_data', label: 'Raw Package Data' },
								],
								raw_package: {
									collapsed_by_default: true,
									technical_label: 'Technical (Read-Only)',
									read_only: true,
									visible_for_advanced_users: true,
								},
								editing: { enabled: false, reason: 'Read-only.' },
								source_mappings: { targets: [], rows: [] },
							},
							audit: { rows: [] },
						},
					},
				}),
			});
			return;
		}
		if (!isTemplates) {
			await route.continue();
			return;
		}
		if (opts?.templatesAlwaysFail) {
			await route.fulfill({
				status: 500,
				contentType: 'application/json',
				body: JSON.stringify({ message: { exc: 'Forced list failure for a11y alert.' } }),
			});
			return;
		}
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				message: {
					ok: true,
					rows: [],
					items: [
						{
							version_code: VC_A11Y,
							title: 'PPRA Works — DOC1',
							revision_label: 'Rev April 2022',
							status: 'Active',
							procurement_category: 'Works',
							supported_methods: ['Open Tender'],
							source_authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							used_by_tender_count: 0,
							supersession_status: 'Current',
							action_availability: {
								view_details: { allowed: true, message: 'Allowed' },
								preview_bundle: { allowed: true, message: 'Allowed' },
								new_revision: { allowed: false, message: 'Revision locked for test.' },
								view_usage: { allowed: true, message: 'Allowed' },
							},
						},
					],
					total_count: 1,
					queue: 'active',
					applied_filters: {},
				},
			}),
		});
	});
}

async function routeImportMinimal(page: Page) {
	await page.route('**/api/method/**', async (route) => {
		const req = route.request();
		const url = req.url();
		const body = req.postData() || '';
		if (url.includes('get_std_library_package_sources') || body.includes('get_std_library_package_sources')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						sources: [
							{
								value: 'BUILTIN_SEED_PACKAGE',
								label: 'Built-in Seed Package',
								entries: [{ value: 'X', label: 'Seed entry' }],
							},
						],
					},
				}),
			});
			return;
		}
		if (
			url.includes('get_std_library_action_availability') ||
			body.includes('get_std_library_action_availability')
		) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						actions: [
							{
								action_code: 'IMPORT_OFFICIAL_STD_PACKAGE',
								allowed: true,
								denial_code: null,
								message: 'Allowed',
								requires_confirmation: false,
								risk_level: 'High',
							},
						],
					},
				}),
			});
			return;
		}
		await route.continue();
	});
}

test.describe('STD-LIB-0610 — pack §27 accessibility basics', () => {
	test.describe.configure({ mode: 'serial' });
	test.setTimeout(240_000);

	test('§27 — list load error uses alert live region', async ({ page, baseURL }) => {
		await routeLibraryCore(page, { templatesAlwaysFail: true });

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({ timeout: 90_000 });
		const alertRegion = page.locator('[data-testid="std-library-list-load-error"]');
		await expect(alertRegion).toBeVisible();
		await expect(alertRegion).toHaveAttribute('role', 'alert');
		await expect(alertRegion).toHaveAttribute('aria-live', 'polite');
	});

	test('§27 — library controls: names, search label, tablist, keyboard tabs', async ({
		page,
		baseURL,
	}) => {
		await routeLibraryCore(page);

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		await expect(page.locator('[data-testid="std-library-card-ppra-works-a11y-2022"]')).toBeVisible({
			timeout: 30_000,
		});

		await expect(shell.locator('[data-testid="std-library-search-input"]')).toHaveAttribute(
			'aria-label',
			/official std library|search/i,
		);

		await expect(
			shell.getByRole('button', { name: /import official std package/i }),
		).toBeVisible();
		const filterToggle = shell.locator('[data-testid="std-library-filter-button"]');
		await expect(filterToggle).toHaveAttribute('aria-expanded', 'false');
		await filterToggle.click();
		await expect(filterToggle).toHaveAttribute('aria-expanded', 'true');

		await page.locator('[data-testid="std-library-card-view-details-ppra-works-a11y-2022"]').click();
		const tablist = shell.locator('.std-library-detail-tabs[role="tablist"]');
		await expect(tablist).toBeVisible();
		await expect(tablist).toHaveAttribute('aria-label', /detail tabs/i);

		const summaryTab = page.locator('[data-testid="std-library-tab-summary"]');
		await expect(summaryTab).toHaveAttribute('role', 'tab');
		await expect(summaryTab).toHaveAttribute('aria-selected', 'true');

		await summaryTab.focus();
		await page.keyboard.press('ArrowRight');
		await expect(page.locator('[data-testid="std-library-tab-validation"]')).toHaveAttribute(
			'aria-selected',
			'true',
		);
		await expect(page.locator('[data-testid="std-library-validation-categories"]')).toBeVisible();
		const badge = page.locator('.std-library-validation-badge').first();
		await expect(badge).toHaveText(/passed/i);

		await page.keyboard.press('ArrowRight');
		await expect(page.locator('[data-testid="std-library-tab-bundle-preview"]')).toHaveAttribute(
			'aria-selected',
			'true',
		);
		const outlineBtn = page.locator('[data-testid="std-bundle-outline"] button').first();
		await expect(outlineBtn).toHaveAttribute('aria-current', 'true');

		await page.locator('[data-testid="std-library-tab-supersession"]').click();
		const revBtn = page.locator('[data-testid="std-supersession-create-revision"]');
		await expect(revBtn).toBeDisabled();
		await expect(revBtn).toHaveAttribute('aria-describedby', 'std-supersession-create-revision-reason');
		await expect(page.locator('#std-supersession-create-revision-reason')).toContainText(
			/Cannot revise active/i,
		);

		await page.locator('[data-testid="std-library-tab-bundle-preview"]').click();
		const genBtn = page.locator('[data-testid="std-bundle-generate-preview"]');
		await expect(genBtn).toBeDisabled();
		await expect(genBtn).toHaveAttribute('aria-describedby', 'std-bundle-generate-preview-reason');

		await page.locator('[data-testid="std-library-tab-advanced"]').click();
		await expect(page.locator('[data-testid="std-advanced-intro"]')).toHaveAttribute('role', 'region');
		await expect(page.locator('[data-testid="std-advanced-intro"]')).toHaveAttribute(
			'aria-label',
			/advanced technical view introduction/i,
		);
	});

	test('§27 — summary queue card activates via keyboard; gated header button exposes denial', async ({
		page,
		baseURL,
	}) => {
		await routeLibraryCore(page, {
			denyImport: true,
			denyImportMessage: 'STD-LIB-0610 denial copy for assistive tech.',
		});

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({ timeout: 90_000 });

		const importBtn = page.locator('[data-testid="std-library-import-package-button"]');
		await expect(importBtn).toBeDisabled();
		await expect(importBtn).toHaveAttribute(
			'aria-describedby',
			'std-library-import-package-button-sr-reason',
		);
		await expect(page.locator('#std-library-import-package-button-sr-reason')).toContainText(
			/STD-LIB-0610 denial copy/i,
		);

		await page.locator('[data-testid="std-library-card-needs-attention"]').focus();
		await page.keyboard.press('Enter');
		await expect(page).toHaveURL(/queue=needs_attention/);

		await page.locator('[data-testid="std-library-card-view-details-ppra-works-a11y-2022"]').click();
		const nrBtn = page.locator('[data-testid="std-library-card-new-revision-ppra-works-a11y-2022"]');
		await expect(nrBtn).toBeDisabled();
		await expect(nrBtn).toHaveAttribute(
			'aria-describedby',
			'std-library-card-new-revision-ppra-works-a11y-2022-sr-reason',
		);
	});

	test('§27 — import wizard: step group label and step fields', async ({ page, baseURL }) => {
		await routeImportMinimal(page);

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library/import`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await expect(page.locator('[data-testid="std-package-import-page"]')).toBeVisible({
			timeout: 90_000,
		});
		const stepper = page.locator('[data-testid="std-package-import-stepper"]');
		await expect(stepper).toHaveAttribute('role', 'group');
		await expect(stepper).toHaveAttribute('aria-label', /import wizard steps/i);

		await expect(
			page.locator('label.std-import-field').filter({
				has: page.locator('[data-testid="std-import-package-source-select"]'),
			}),
		).toHaveCount(1);
		await expect(page.getByRole('button', { name: /next/i })).toBeVisible();
		await expect(page.getByRole('button', { name: /cancel/i })).toBeVisible();
	});
});
