/**
 * STD-LIB-0100 — Official STD Library route shell (layout + selectors §6).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator, loginAsProcurementOfficer } from '../../helpers/auth';
import { dismissOptionalDeskModals, openWorkspaceFromDeskLauncher } from '../../helpers/routes';
import { procurementModule } from '../../helpers/selectors';

test.describe('Official STD Library shell (STD-LIB-0100)', () => {
	test.setTimeout(180_000);

	test('std-engine normalizes to library and renders shell', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page).toHaveURL(/std-engine\/library|library/i, { timeout: 90_000 });
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-header-title"]')).toHaveText(
			'Official STD Library',
			{ timeout: 30_000 },
		);
		await expect(shell.locator('[data-testid="std-library-header-subtitle"]')).toContainText(
			'Manage official standard tender documents available for tender preparation.',
		);
	});

	test('std-engine/library renders regions A–F and primary action', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-guidance-strip"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-summary-cards"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-search-input"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-filter-button"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-list"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-detail-panel"]')).toBeVisible();
		await expect(
			shell.locator('[data-testid="std-library-import-package-button"]'),
		).toHaveText('Import Official STD Package');
		await expect(
			shell.locator('[data-testid="std-library-register-source-button"]'),
		).toHaveText('Register Source Document');
		await expect(
			shell.locator('[data-testid="std-library-validate-library-button"]'),
		).toHaveText('Validate Library');
		await expect(shell.locator('[data-testid="std-library-guidance-strip"]')).toHaveText(
			'Official STDs are imported as structured packages. Source files are retained as evidence. Active versions are immutable.',
		);
		for (const sel of [
			'std-library-card-active',
			'std-library-card-needs-attention',
			'std-library-card-ready-review',
			'std-library-card-superseded',
			'std-library-card-package-imports',
			'std-library-card-bundle-issues',
		]) {
			await expect(shell.locator(`[data-testid="${sel}"]`)).toBeVisible();
		}
	});

	test('shell does not expose Create STD Instance', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell).not.toContainText('Create STD Instance');
		await expect(shell).not.toContainText('Add Evaluation Criteria');
		await expect(shell).not.toContainText('Configure Bid Opening');
		await expect(shell).not.toContainText('Generate Contract');
		await expect(shell).not.toContainText('Upload STD as Tender Document');
	});

	test('UI-HARD-0210 — Procurement Officer cannot access Official STD Library advanced tab', async ({
		page,
		baseURL,
	}) => {
		await loginAsProcurementOfficer(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`, { waitUntil: 'domcontentloaded' });
		await dismissOptionalDeskModals(page);
		await page.waitForLoadState('load').catch(() => {});
		/* Align with §26 item 23 (pack smoke): officer has no Page role — shell never mounts. */
		await expect(page.locator('[data-testid="std-library-page"]')).toHaveCount(0, { timeout: 90_000 });
		await expect(page.locator('[data-testid="std-library-tab-advanced"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="std-advanced-technical-view"]')).toHaveCount(0);
	});

	test('UI-HARD-0200 — sentinel selector, advanced disclosure default-closed, prohibited CTAs absent', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-create-instance-button-absent"]')).toBeAttached();
		await expect(shell.locator('[data-testid="std-library-advanced-view-toggle"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-advanced-catalogue-open"]')).toBeHidden();
		for (const phrase of [
			'Create STD Instance',
			'Release to Tender',
			'Configure Tender Document',
			'Approve Tender',
			'Publish Tender',
		]) {
			await expect(shell).not.toContainText(phrase);
		}
	});

	test('register source document panel opens and shows non-activation warning', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_action_availability*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						actions: [
							{
								action_code: 'REGISTER_SOURCE_DOCUMENT',
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
		});
		await page.route('**/api/method/**register_std_library_source_document*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						source_document: {
							source_document_code: 'PPRA-WORKS-2022-04-PDF',
							activation_status: 'Not Activated',
						},
						message:
							'Source document registered as evidence. This does not make an STD available for tenders.',
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await page.locator('[data-testid="std-library-register-source-button"]').click();
		await expect(page.locator('[data-testid="std-library-action-modal"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-action-modal-title"]')).toContainText(
			'Register source evidence',
		);
		await expect(page.locator('[data-testid="std-register-source-scope-hint"]')).toContainText(
			'Library-wide',
		);
		await expect(page.locator('[data-testid="std-library-validation-summary-panel"]')).toBeHidden();
		await expect(page.locator('[data-testid="std-register-source-panel"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-register-source-code"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-register-source-title"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-register-source-authority"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-register-source-revision"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-register-source-save"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-register-source-warning"]')).toContainText(
			'does not make it available for tenders',
		);

		await page.locator('[data-testid="std-register-source-code"]').fill('PPRA-WORKS-2022-04-PDF');
		await page
			.locator('[data-testid="std-register-source-title"]')
			.fill('PPRA Works Building STD Source PDF');
		await page.locator('[data-testid="std-register-source-authority"]').fill('PPRA');
		await page.locator('[data-testid="std-register-source-revision"]').fill('Rev April 2022');
		await page.locator('[data-testid="std-register-source-save"]').click();
		await expect(page.locator('[data-testid="std-register-source-panel"]')).toContainText(
			'does not make an STD available for tenders',
		);

		await page.locator('[data-testid="std-library-action-modal-close"]').click();
		await expect(page.locator('[data-testid="std-library-action-modal"]')).toBeHidden();
	});

	test('validate library panel shows summary rows and failed row links to validation tab', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_action_availability*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						actions: [
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
		});
		await page.route('**/api/method/**get_std_library_validation_summary*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [
							{
								version_code: 'ACTIVE-STD',
								version: 'Active STD',
								status: 'Active',
								last_validated: '2026-05-08 18:30:00',
								result: 'Passed',
								blockers: 0,
								bundle_status: 'Available',
							},
							{
								version_code: 'BLOCKED-STD',
								version: 'Blocked STD',
								status: 'Draft',
								last_validated: '2026-05-08 18:32:00',
								result: 'Blocked',
								blockers: 2,
								bundle_status: 'Failed',
							},
						],
						message: 'Validation summary loaded.',
					},
				}),
			});
		});
		await page.route('**/api/method/**run_std_library_validation*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [
							{
								version_code: 'BLOCKED-STD',
								version: 'Blocked STD',
								status: 'Draft',
								last_validated: '2026-05-08 18:35:00',
								result: 'Blocked',
								blockers: 2,
								bundle_status: 'Failed',
							},
						],
						message: 'Validation run completed for eligible STD versions.',
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [
							{
								version_code: 'BLOCKED-STD',
								title: 'Blocked STD',
								revision_label: 'Rev 1',
								status: 'Draft',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Blocked',
								bundle_preview_status: 'Failed',
								used_by_tender_count: 0,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
									new_revision: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Blocked STD',
							version_code: 'BLOCKED-STD',
							revision_label: 'Rev 1',
							status: 'Draft',
							authority: 'PPRA',
							validation_status: 'Blocked',
							bundle_preview_status: 'Failed',
							validation: {
								overall: 'Blocked',
								last_validated: '2026-05-08 18:35:00',
								categories: [],
								findings: [],
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await page.locator('[data-testid="std-library-validate-library-button"]').click();
		await expect(page.locator('[data-testid="std-library-action-modal"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-action-modal-title"]')).toContainText(
			'Library-wide validation',
		);
		await expect(page.locator('[data-testid="std-library-validation-scope-hint"]')).toContainText(
			'not limited',
		);
		await expect(page.locator('[data-testid="std-register-source-panel"]')).toBeHidden();
		await expect(page.locator('[data-testid="std-library-validation-summary-panel"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-run-validation"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-validation-summary-row"]')).toHaveCount(2);
		await page.locator('[data-testid="std-library-run-validation"]').click();
		await expect(page.locator('[data-testid="std-library-validation-summary-panel"]')).toContainText(
			'Validation run completed for eligible STD versions.',
		);
		await page
			.locator('[data-testid="std-library-validation-summary-row"]')
			.filter({ hasText: 'Blocked STD' })
			.first()
			.click();
		await expect(page.locator('[data-testid="std-library-tab-validation"]')).toHaveClass(/is-active/);
	});

	test('denied action shows disabled button with explanation', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_action_availability*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						actions: [
							{
								action_code: 'IMPORT_OFFICIAL_STD_PACKAGE',
								allowed: false,
								denial_code: 'STD_AUTH_PERMISSION_DENIED',
								message: 'Unavailable: you do not have permission to import official STD packages.',
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
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const importButton = page.locator('[data-testid="std-library-import-package-button"]');
		await expect(importButton).toBeVisible({ timeout: 90_000 });
		await expect(importButton).toBeDisabled();
		await expect(importButton).toHaveAttribute(
			'title',
			'Unavailable: you do not have permission to import official STD packages.',
		);
	});

	test('administrator gets enabled import action from live availability endpoint', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const importButton = page.locator('[data-testid="std-library-import-package-button"]');
		await expect(importButton).toBeVisible({ timeout: 90_000 });
		await expect(importButton).toBeEnabled();
		await expect(importButton).not.toHaveAttribute('title', /temporarily not available/i);
	});

	test('import action opens package wizard shell with six-step gating scaffold', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_action_availability*', async (route) => {
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
		});
		await page.route('**/api/method/**get_std_library_package_sources*', async (route) => {
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
								entries: [
									{
										value: 'PPRA-WORKS-BLDG-2022-04',
										label: 'PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022',
									},
								],
							},
							{
								value: 'UPLOADED_STRUCTURED_PACKAGE',
								label: 'Uploaded Structured Package',
								entries: [],
							},
							{
								value: 'CONNECTED_REGISTRY',
								label: 'Connected Registry',
								entries: [],
							},
						],
					},
				}),
			});
		});
		await page.route('**/api/method/**select_std_library_import_package*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						metadata: {
							package_type: 'Works STD Structured Package',
							expected_std_category: 'WORKS',
							package_version: 'Rev April 2022',
						},
						selection: {
							package_source: 'BUILTIN_SEED_PACKAGE',
							package_entry: 'PPRA-WORKS-BLDG-2022-04',
						},
					},
				}),
			});
		});
		await page.route('**/api/method/**save_std_library_source_evidence*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						source_evidence: {
							source_authority: 'PPRA',
							source_title: 'KE-PPRA-WORKS-BLDG-2022-04-POC',
							source_revision: 'Rev April 2022',
							review_status: 'Draft',
						},
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_detected_structure*', async (route) => {
			await new Promise((resolve) => setTimeout(resolve, 350));
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						summary: {
							parts_sections: '3 parts, 10 sections detected',
							locked_legal_text: 'ITT and GCC detected',
							parameters: '48 TDS/SCC parameters detected',
							forms: '14 tendering forms, 9 contract forms detected',
							boq_rules: 'Works BOQ rules detected',
							source_mappings:
								'Bundle, Submission, Opening, Evaluation, Contract mappings detected',
							readiness_rules: '16 readiness rules detected',
							works_boq_applicable: true,
						},
						technical_details: {
							sections: ['Part I', 'Part II'],
							parameter_groups: ['Eligibility', 'Evaluation'],
							form_categories: ['Tendering Forms (14)', 'Contract Forms (9)'],
							mapping_coverage: {
								bundle: 12,
								submission: 10,
								opening: 8,
								evaluation: 14,
								contract: 9,
							},
						},
					},
				}),
			});
		});
		await page.route('**/api/method/**run_std_library_import_validation*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						validation: {
							result: 'Needs Attention',
							summary:
								'2 blockers must be resolved before this STD can be reviewed or activated.',
							categories: [
								{ key: 'sections', status: 'Passed' },
								{ key: 'locked_legal_text', status: 'Passed' },
								{ key: 'parameters', status: 'Needs Attention' },
								{ key: 'forms', status: 'Passed' },
								{ key: 'boq_rules', status: 'Passed' },
								{ key: 'source_mappings', status: 'Blocked' },
								{ key: 'generated_models', status: 'Needs Attention' },
								{ key: 'bundle_rendering', status: 'Passed' },
							],
							blockers: [
								{
									category: 'Source Mappings',
									reason: 'Evaluation Rules mapping is incomplete.',
									fix_path: 'Open Advanced Technical View -> Source Mappings.',
									code: 'DEM_MAPPING_MISSING',
								},
							],
						},
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_import_validation*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						validation: {
							result: 'Needs Attention',
							summary:
								'2 blockers must be resolved before this STD can be reviewed or activated.',
							categories: [
								{ key: 'sections', status: 'Passed' },
								{ key: 'locked_legal_text', status: 'Passed' },
								{ key: 'parameters', status: 'Needs Attention' },
								{ key: 'forms', status: 'Passed' },
								{ key: 'boq_rules', status: 'Passed' },
								{ key: 'source_mappings', status: 'Blocked' },
								{ key: 'generated_models', status: 'Needs Attention' },
								{ key: 'bundle_rendering', status: 'Passed' },
							],
							blockers: [
								{
									category: 'Source Mappings',
									reason: 'Evaluation Rules mapping is incomplete.',
									fix_path: 'Open Advanced Technical View -> Source Mappings.',
									code: 'DEM_MAPPING_MISSING',
								},
							],
						},
					},
				}),
			});
		});
		await page.route('**/api/method/**generate_std_library_bundle_preview*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						status: 'Preview generated',
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_bundle_preview*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						outline: [
							{ number: '0', title: 'Invitation to Tender' },
							{ number: 'I', title: 'Section I — Instructions to Tenderers' },
							{ number: 'II', title: 'Section II — Tender Data Sheet' },
							{ number: 'III', title: 'Section III — Evaluation and Qualification Criteria' },
							{ number: 'IV', title: 'Section IV — Tendering Forms' },
							{ number: 'V', title: 'Section V — Bills of Quantities' },
							{ number: 'VI', title: 'Section VI — Specifications' },
							{ number: 'VII', title: 'Section VII — Drawings' },
							{ number: 'VIII', title: 'Section VIII — General Conditions of Contract' },
							{ number: 'IX', title: 'Section IX — Special Conditions of Contract' },
							{ number: 'X', title: 'Section X — Contract Forms' },
						],
						sections: [
							{
								number: '0',
								title: 'Invitation to Tender',
								preview: 'Invitation to Tender content preview is available.',
							},
						],
						actions: {
							preview_in_browser: true,
							download_pdf: true,
							download_docx: true,
							view_placeholder_list: true,
						},
						message: 'Bundle preview is ready for review.',
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_placeholder_list*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						placeholders: [
							'[To be completed during tender preparation: Submission Deadline]',
							'[To be completed during tender preparation: Employer Name]',
							'[To be completed during tender preparation: BOQ Items and Quantities]',
						],
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_import_final_review*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						summary: {
							std_title: 'PPRA Works — Building and Associated Civil Engineering Works',
							revision: 'Rev April 2022',
							source_authority: 'PPRA',
							source_evidence_status: 'Evidence captured',
							validation_result: 'Passed',
							bundle_preview_status: 'Available',
							generated_model_status: 'Ready',
							warnings: ['Tender preparation placeholders must be completed before issue.'],
						},
						blockers: [],
						actions: {
							review_required: true,
							can_submit_review: true,
							can_activate: false,
							activate_denial_code: 'STD_REVIEW_REQUIRED',
						},
						status: 'Ready for Review',
						confirmation_text: {
							submit:
								'This will submit the structured STD package for legal or policy review. It will not be available for tenders until approved and activated.',
							activate:
								'This will activate the STD version for future tenders. Active versions are immutable.',
						},
					},
				}),
			});
		});
		await page.route('**/api/method/**submit_std_library_import_review*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						import_code: 'STD-IMPORT-DRAFT',
						status: 'Submitted for Review',
						message: 'Package submitted for legal or policy review.',
					},
				}),
			});
		});
		await page.route('**/api/method/**activate_std_library_import*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: false,
						import_code: 'STD-IMPORT-DRAFT',
						status: 'Activation Blocked',
						message: 'This package cannot be activated yet. Complete governance review first.',
						denial_code: 'STD_REVIEW_REQUIRED',
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await dismissOptionalDeskModals(page);

		await page.locator('[data-testid="std-library-import-package-button"]').click();
		await expect(page).toHaveURL(/std-engine\/library\/import/i, { timeout: 90_000 });
		await expect(page.locator('[data-testid="std-package-import-page"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('[data-testid="std-package-import-stepper"]')).toBeVisible();
		await expect(page.locator('.std-package-import-step')).toHaveCount(6);
		await expect(page.locator('[data-testid="std-package-import-back"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-package-import-save-draft"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-package-import-cancel"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-package-source-select"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-package-file-picker"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-package-type"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-package-category"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-raw-file-warning"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeDisabled();
		await expect(page.locator('.std-package-import-step[data-step-index="1"]')).toBeDisabled();

		await page.locator('[data-testid="std-import-package-source-select"]').selectOption(
			'BUILTIN_SEED_PACKAGE',
		);
		await page.locator('[data-testid="std-import-package-file-picker"]').selectOption(
			'PPRA-WORKS-BLDG-2022-04',
		);
		await expect(page.locator('[data-testid="std-import-package-type"]')).toHaveText(
			'Works STD Structured Package',
		);
		await expect(page.locator('[data-testid="std-import-package-category"]')).toHaveText('WORKS');
		await expect(page.locator('[data-testid="std-import-package-version"]')).toHaveText(
			'Rev April 2022',
		);
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeEnabled();
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'2. Confirm Source Evidence',
		);
		await expect(page.locator('[data-testid="std-import-source-authority"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-source-authority"]')).toHaveValue('PPRA');
		await expect(page.locator('[data-testid="std-import-source-title"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-source-title"]')).toHaveValue(
			'PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022',
		);
		await expect(page.locator('[data-testid="std-import-source-revision"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-source-revision"]')).toHaveValue(
			'Rev April 2022',
		);
		await expect(page.locator('[data-testid="std-import-source-file"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-source-hash"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-source-guidance"]')).toContainText(
			'official document is retained as evidence',
		);
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeEnabled();
		await page.locator('[data-testid="std-import-source-authority"]').fill('PPRA');
		await page.locator('[data-testid="std-import-source-title"]').fill(
			'KE-PPRA-WORKS-BLDG-2022-04-POC',
		);
		await page.locator('[data-testid="std-import-source-revision"]').fill('Rev April 2022');
		await page.locator('[data-testid="std-import-source-review-status"]').selectOption('Draft');
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeEnabled();
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'3. Review Detected Structure',
		);
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeDisabled();
		await expect(page.locator('[data-testid="std-import-detected-structure"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-detected-sections"]')).toContainText(
			'3 parts, 10 sections detected',
		);
		await expect(page.locator('[data-testid="std-import-detected-parameters"]')).toContainText(
			'48 TDS/SCC parameters detected',
		);
		await expect(page.locator('[data-testid="std-import-detected-forms"]')).toContainText(
			'14 tendering forms, 9 contract forms detected',
		);
		await expect(page.locator('[data-testid="std-import-detected-boq-rules"]')).toContainText(
			'Works BOQ rules detected',
		);
		await expect(page.locator('[data-testid="std-import-detected-mappings"]')).toContainText(
			'Bundle, Submission, Opening, Evaluation, Contract mappings detected',
		);
		await expect(page.locator('[data-testid="std-import-expand-technical-details"]')).toBeVisible();
		await page.locator('[data-testid="std-import-expand-technical-details"]').click();
		await expect(page.locator('.std-import-detected-technical')).toContainText(
			'Parameter groups:',
		);
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeEnabled();
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'4. Validate Structured Model',
		);
		await expect(page.locator('[data-testid="std-import-validation-summary"]')).toContainText(
			'Validation Result: Needs Attention',
		);
		await expect(
			page.locator('[data-testid="std-import-validation-category-sections"]'),
		).toContainText('Passed');
		await expect(
			page.locator('[data-testid="std-import-validation-category-mappings"]'),
		).toContainText('Blocked');
		await expect(page.locator('[data-testid="std-import-validation-blockers"]')).toContainText(
			'Open Advanced Technical View -> Source Mappings.',
		);
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeEnabled();
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'5. Preview Tender Bundle',
		);
		await expect(page.locator('[data-testid="std-import-bundle-preview"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-bundle-outline"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-bundle-section-1"]')).toContainText(
			'Invitation to Tender',
		);
		await expect(page.locator('[data-testid="std-import-placeholder-list"]')).toContainText(
			'To be completed during tender preparation',
		);
		await expect(page.locator('[data-testid="std-import-download-pdf"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-download-docx"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeEnabled();
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'6. Submit for Review / Activate',
		);
		await expect(page.locator('[data-testid="std-import-final-summary"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-final-summary"]')).toContainText(
			'PPRA Works — Building and Associated Civil Engineering Works',
		);
		await expect(page.locator('[data-testid="std-import-final-blockers"]')).toContainText(
			'No finalization blockers detected.',
		);
		await expect(page.locator('[data-testid="std-import-final-confirmation"]')).toContainText(
			'legal or policy review',
		);
		await expect(page.locator('[data-testid="std-import-submit-review"]')).toBeEnabled();
		await expect(page.locator('[data-testid="std-import-activate"]')).toBeDisabled();
		await expect(page.locator('[data-testid="std-package-import-next"]')).toBeDisabled();
		await page.locator('[data-testid="std-import-submit-review"]').click();
		await expect(page.locator('[data-testid="std-import-submit-review"]')).toBeDisabled();
		await expect(page.locator('.std-import-step6')).toContainText('Submitted for Review');
		await expect(page.locator('[data-testid="std-package-import-page"]')).toContainText(
			'structured package workflow',
		);
		await expect(page.locator('[data-testid="std-package-import-page"]')).not.toContainText(
			'Upload PDF',
		);
	});

	test('summary cards use API counts and queue click updates URL/query context', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_summary_counts*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						active_count: 4,
						needs_attention_count: 2,
						ready_for_review_count: 3,
						superseded_count: 1,
						package_import_count: 6,
						bundle_issue_count: 5,
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const activeCard = page.locator('[data-testid="std-library-card-active"]');
		await expect(activeCard).toContainText('4');
		const queueCard = page.locator('[data-testid="std-library-card-needs-attention"]');
		await queueCard.click();
		await expect(queueCard).toHaveAttribute('aria-pressed', 'true');
		await expect(page).toHaveURL(/queue=needs_attention/);
		await expect(page.locator('[data-testid="std-library-list-queue-context"]')).toContainText(
			'Needs Attention:',
		);
	});

	test('filters panel, chips, and clear reset URL state', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						total_count: 8,
						queue: 'active',
						applied_filters: {},
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await expect(page.locator('[data-testid="std-library-search-input"]')).toHaveAttribute(
			'placeholder',
			'Search by STD title, revision, authority, category, method, or source document',
		);
		await page.locator('[data-testid="std-library-filter-button"]').click();
		await expect(page.locator('[data-testid="std-library-filter-panel"]')).toBeVisible();
		await page.locator('[data-testid="std-library-search-input"]').fill('works');
		await page.locator('[data-testid="std-library-search-input"]').blur();
		await expect(page.locator('[data-testid="std-library-active-filter-chips"]')).toContainText(
			'Search: works',
		);
		await expect(page).toHaveURL(/search=works/);
		await page.locator('[data-testid="std-library-clear-filters"]').click();
		await expect(page.locator('[data-testid="std-library-active-filter-chips"]')).toContainText(
			'No active filters.',
		);
		await expect(page).not.toHaveURL(/search=works/);
	});

	test('queue and filters coexist in URL and context', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						total_count: 2,
						queue: 'needs_attention',
						applied_filters: {},
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-search-input"]').fill('PPRA');
		await page.locator('[data-testid="std-library-search-input"]').blur();
		await page.locator('[data-testid="std-library-card-needs-attention"]').click();
		await expect(page).toHaveURL(/queue=needs_attention/);
		await expect(page).toHaveURL(/search=PPRA|search=ppra/);
		await expect(page.locator('[data-testid="std-library-list-queue-context"]')).toContainText(
			'Needs Attention: 2 item(s).',
		);
	});

	test('STD-LIB-0520: URL std_code and tab=bundle deep link restores Bundle Preview after load and reload', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const versionCode = 'STDTV-WORKS-BUILDING-REV-APR-2022';
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: versionCode,
								title: 'PPRA Works — Building',
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
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
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
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'PPRA Works — Building',
							version_code: versionCode,
							revision_label: 'Rev April 2022',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: {
								identity: {
									title: 'PPRA Works — Building',
									revision: 'Rev April 2022',
									authority: 'PPRA',
									template_family: 'STD-WORKS',
								},
								source_evidence: {
									source_document: 'DOC1',
									source_file: 'Available',
									source_hash: 'Available',
									evidence_status: 'Registered',
								},
								supported_use: {
									category: 'Works',
									methods: ['Open Tender'],
									contract_type: 'Admeasurement / Unit Rate',
									requires_boq: 'Yes',
								},
								health_summary: {
									validation: 'Passed',
									bundle_preview: 'Available',
									generated_models: 'Available',
								},
								output_summary: {
									line: 'Structured template outputs are ready for controlled tender assembly.',
								},
								next_action: {
									status: 'Active',
									action: 'Preview bundle or create new revision.',
								},
							},
							bundle_preview: {
								status_bar: {
									preview_status: 'Available',
									last_generated: '2026-05-08 16:00',
									output_type: 'Template-level preview',
									placeholder_count: 48,
									render_warnings: 0,
								},
								outline: ['Invitation to Tender'],
								preview_blocks: [
									{
										section: 'Invitation to Tender',
										content:
											'Official invitation and submission instructions for qualified tenderers.',
									},
								],
								placeholders: [],
								actions: {
									generate_preview: { allowed: true, visible: true, message: 'Allowed' },
									download_pdf: { allowed: true, visible: true, message: 'Allowed' },
									download_docx: { allowed: true, visible: true, message: 'Allowed' },
									view_placeholders: { allowed: true, visible: true, message: 'Allowed' },
								},
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		const q = new URLSearchParams({
			queue: 'active',
			std_code: versionCode,
			tab: 'bundle',
		});
		await page.goto(`${root}/app/std-engine/library?${q.toString()}`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const bundleTabBtn = page.locator('[data-testid="std-library-tab-bundle-preview"]');
		await expect(bundleTabBtn).toHaveClass(/is-active/);
		await expect(page.locator('[data-testid="std-library-bundle-tab"]')).toBeVisible();
		await expect(page).toHaveURL(new RegExp(`std_code=${versionCode.replace(/-/g, '\\-')}`));
		await expect(page).toHaveURL(/tab=bundle/);

		await page.reload();
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(bundleTabBtn).toHaveClass(/is-active/);
		await expect(page.locator('[data-testid="std-library-bundle-tab"]')).toBeVisible();
		await expect(page).toHaveURL(/tab=bundle/);
	});

	test('STD-LIB-0530: active queue empty state uses formal pack copy', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [],
						total_count: 0,
						queue: 'active',
						applied_filters: {},
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library?queue=active`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const emptyBox = page.locator('[data-testid="std-library-list-empty"]');
		await expect(emptyBox).toBeVisible();
		await expect(emptyBox).toContainText('No active STD versions are available.');
		await expect(emptyBox).toContainText(
			'An STD must be imported, validated, reviewed, and activated before tenders can use it.',
		);
	});

	test('STD-LIB-0530: needs_attention queue empty state uses pack copy', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [],
						total_count: 0,
						queue: 'needs_attention',
						applied_filters: {},
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library?queue=needs_attention`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const emptyBox = page.locator('[data-testid="std-library-list-empty"]');
		await expect(emptyBox).toBeVisible();
		await expect(emptyBox).toContainText('No STD versions currently require attention.');
	});

	test('STD-LIB-0530: list load failure shows safe message and Retry', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.abort('failed');
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-library-list-load-error"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-list-retry"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-page"]')).not.toContainText('Traceback');
	});

	test('STD-LIB-0530: Bundle Preview tab shows empty-state panel when preview has no blocks', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'BUNDLE-EMPTY-0530',
								title: 'Empty Bundle STD',
								revision_label: 'Rev 1',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Passed',
								bundle_preview_status: 'Not Generated',
								used_by_tender_count: 0,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
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
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Empty Bundle STD',
							version_code: 'BUNDLE-EMPTY-0530',
							revision_label: 'Rev 1',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Not Generated',
							state_banner: 'Review status.',
							summary: {
								identity: {
									title: 'Empty Bundle STD',
									revision: 'Rev 1',
									authority: 'PPRA',
									template_family: 'STD-WORKS',
								},
								source_evidence: {
									source_document: 'DOC',
									source_file: 'Available',
									source_hash: 'Available',
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
									bundle_preview: 'Not Generated',
									generated_models: '—',
								},
								output_summary: { line: '—' },
								next_action: { status: 'Active', action: 'Generate bundle preview.' },
							},
							bundle_preview: {
								status_bar: {
									preview_status: 'Not Generated',
									last_generated: '',
									output_type: 'Template-level preview',
									placeholder_count: 0,
									render_warnings: 0,
								},
								outline: [],
								preview_blocks: [],
								placeholders: [],
								actions: {
									generate_preview: { allowed: true, visible: true, message: 'Allowed' },
									download_pdf: { allowed: false, visible: false, message: 'Unavailable' },
									download_docx: { allowed: false, visible: false, message: 'Unavailable' },
									view_placeholders: { allowed: true, visible: true, message: 'Allowed' },
								},
							},
						},
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-bundle-empty-0530"]').click();
		await page.locator('[data-testid="std-library-tab-bundle-preview"]').click();
		const emptyPanel = page.locator('[data-testid="std-library-bundle-empty"]');
		await expect(emptyPanel).toBeVisible();
		await expect(emptyPanel).toContainText('No bundle preview has been generated yet.');
		await expect(emptyPanel).toContainText(
			'Generate a preview to review the recombined tender document.',
		);
	});

	test('library cards render with dynamic selectors and prohibited action absent', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'STDTV-WORKS-BUILDING-REV-APR-2022',
								title: 'PPRA Works — Building and Associated Civil Engineering Works',
								revision_label: 'Rev April 2022',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender', 'Restricted Tender'],
								source_authority: 'PPRA',
								validation_status: 'Passed',
								bundle_preview_status: 'Available',
								used_by_tender_count: 12,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
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

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(
			page.locator('[data-testid="std-library-card-stdtv-works-building-rev-apr-2022"]'),
		).toBeVisible();
		await expect(
			page.locator('[data-testid="std-library-card-title-stdtv-works-building-rev-apr-2022"]'),
		).toContainText('PPRA Works');
		await expect(
			page.locator('[data-testid="std-library-card-preview-bundle-stdtv-works-building-rev-apr-2022"]'),
		).toBeVisible();
		await expect(
			page.locator('[data-testid="std-library-card-new-revision-stdtv-works-building-rev-apr-2022"]'),
		).toBeVisible();
		await expect(page.locator('[data-testid="std-library-list"]')).not.toContainText(
			'Create STD Instance',
		);
	});

	test('card details action updates selected detail placeholder', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'STD-ONE',
								title: 'STD One',
								revision_label: 'Rev 1',
								status: 'Ready for Review',
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
									validate: { allowed: true, message: 'Allowed' },
									submit_for_review: { allowed: true, message: 'Allowed' },
									new_revision: { allowed: false, message: 'Unavailable' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
						queue: 'ready_review',
						applied_filters: {},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-std-one"]').click();
		await expect(page.locator('[data-testid="std-library-detail-panel"]')).toContainText(
			'STD One',
		);
		await expect(page.locator('[data-testid="std-library-detail-header"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-detail-state-banner"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-summary"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-validation"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-bundle-preview"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-usage"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-supersession"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-advanced"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-tab-audit"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-detail-state-banner"]')).toContainText(
			'Review this STD version status before proceeding.',
		);
		await expect(page.locator('[data-testid="std-library-summary-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-identity"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-source-evidence"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-supported-use"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-health"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-next-action"]')).toBeVisible();
	});

	test('detail banner matches active and imported draft status mapping', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'ACTIVE-STD',
								title: 'Active STD',
								revision_label: 'Rev 2',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Passed',
								bundle_preview_status: 'Available',
								used_by_tender_count: 1,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Active STD',
							version_code: 'ACTIVE-STD',
							revision_label: 'Rev 2',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: {
								identity: {
									title: 'Active STD',
									revision: 'Rev 2',
									authority: 'PPRA',
									template_family: 'STD-WORKS',
								},
								source_evidence: {
									source_document: 'DOC1-WORKS',
									source_file: 'Available',
									source_hash: 'Available',
									evidence_status: 'Registered',
								},
								supported_use: {
									category: 'Works',
									methods: ['Open Tender'],
									contract_type: 'Admeasurement / Unit Rate',
									requires_boq: 'Yes',
								},
								health_summary: {
									validation: 'Passed',
									bundle_preview: 'Available',
									generated_models: 'Available',
								},
								output_summary: {
									line: 'Structured template outputs are ready for controlled tender assembly.',
								},
								next_action: {
									status: 'Active',
									action: 'Preview bundle or create new revision.',
								},
							},
						},
					},
				}),
			});
		});
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-active-std"]').click();
		await expect(page.locator('[data-testid="std-library-detail-state-banner"]')).toContainText(
			'active and immutable',
		);
		await expect(page.locator('[data-testid="std-library-summary-next-action"]')).toContainText(
			'Preview bundle or create new revision.',
		);
		await expect(page.locator('[data-testid="std-library-summary-tab"]')).not.toContainText('raw json');
		await expect(page.locator('[data-testid="std-library-summary-tab"]')).not.toContainText('xml');
	});

	test('validation tab shows category health and findings with business-facing copy', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'VAL-STD',
								title: 'Validation STD',
								revision_label: 'Rev 4',
								status: 'Needs Attention',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Blocked',
								bundle_preview_status: 'Needs Tender Values',
								used_by_tender_count: 0,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: false, message: 'Unavailable' },
									validate: { allowed: true, message: 'Allowed' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: false, message: 'Unavailable' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Validation STD',
							version_code: 'VAL-STD',
							revision_label: 'Rev 4',
							status: 'Needs Attention',
							authority: 'PPRA',
							validation_status: 'Blocked',
							bundle_preview_status: 'Needs Tender Values',
							state_banner:
								'This STD package needs attention before it can be reviewed or activated.',
							summary: {
								identity: {
									title: 'Validation STD',
									revision: 'Rev 4',
									authority: 'PPRA',
									template_family: 'STD-WORKS',
								},
								source_evidence: {
									source_document: 'DOC-VAL',
									source_file: 'Available',
									source_hash: 'Available',
									evidence_status: 'Registered',
								},
								supported_use: {
									category: 'Works',
									methods: ['Open Tender'],
									contract_type: 'Admeasurement / Unit Rate',
									requires_boq: 'Yes',
								},
								health_summary: {
									validation: 'Blocked',
									bundle_preview: 'Needs Tender Values',
									generated_models: 'Available',
								},
								output_summary: {
									line: 'Structured template outputs are ready for controlled tender assembly.',
								},
								next_action: {
									status: 'Needs Attention',
									action: 'Resolve validation blockers.',
								},
							},
							validation: {
								overall_status: 'Blocked',
								severity: 'High',
								categories: [
									{ category: 'Structure Integrity', state: 'Blocked' },
									{ category: 'Source Mappings', state: 'Blocked' },
								],
								issues: ['Mandatory placeholders are incomplete for at least one required section.'],
								remediation: 'Resolve blocked categories and re-run validation.',
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-val-std"]').click();
		await page.locator('[data-testid="std-library-tab-validation"]').click();
		await expect(page.locator('[data-testid="std-library-validation-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-validation-categories"]')).toContainText(
			'Structure Integrity',
		);
		await expect(page.locator('[data-testid="std-library-validation-findings"]')).toContainText(
			'Remediation',
		);
		await expect(page.locator('[data-testid="std-library-validation-tab"]')).not.toContainText(
			'raw json',
		);
		await expect(page.locator('[data-testid="std-library-validation-tab"]')).not.toContainText(
			'<xml',
		);
	});

	test('bundle preview tab renders status, outline, placeholders, and gated downloads', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'BUNDLE-STD',
								title: 'Bundle STD',
								revision_label: 'Rev 2',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Passed',
								bundle_preview_status: 'Available',
								used_by_tender_count: 2,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Bundle STD',
							version_code: 'BUNDLE-STD',
							revision_label: 'Rev 2',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: {
								identity: {
									title: 'Bundle STD',
									revision: 'Rev 2',
									authority: 'PPRA',
									template_family: 'STD-WORKS',
								},
								source_evidence: {
									source_document: 'DOC-BUNDLE',
									source_file: 'Available',
									source_hash: 'Available',
									evidence_status: 'Registered',
								},
								supported_use: {
									category: 'Works',
									methods: ['Open Tender'],
									contract_type: 'Admeasurement / Unit Rate',
									requires_boq: 'Yes',
								},
								health_summary: {
									validation: 'Passed',
									bundle_preview: 'Available',
									generated_models: 'Available',
								},
								output_summary: {
									line: 'Structured template outputs are ready for controlled tender assembly.',
								},
								next_action: {
									status: 'Active',
									action: 'Preview bundle or create new revision.',
								},
							},
							validation: {
								overall_status: 'Passed',
								severity: 'Low',
								categories: [{ category: 'Structure Integrity', state: 'Passed' }],
								issues: [],
								remediation: 'No immediate remediation required.',
							},
							bundle_preview: {
								status_bar: {
									preview_status: 'Available',
									last_generated: '2026-05-08 16:00',
									output_type: 'Template-level preview',
									placeholder_count: 48,
									render_warnings: 0,
								},
								outline: ['Invitation to Tender', 'I. Instructions to Tenderers'],
								preview_blocks: [
									{
										section: 'Invitation to Tender',
										content:
											'Official invitation and submission instructions for qualified tenderers.',
									},
									{
										section: 'I. Instructions to Tenderers',
										content: 'Operational instructions for submissions and responsiveness.',
									},
								],
								placeholders: [
									{
										group: 'Tender Identity',
										rows: [
											{
												label: 'Tender Number',
												filled_during: 'Tender preparation',
												source_section: 'TDS',
												output_impact: 'Bundle, DSM',
											},
										],
									},
								],
								actions: {
									generate_preview: { allowed: true, visible: true, message: 'Allowed' },
									download_pdf: { allowed: true, visible: true, message: 'Allowed' },
									download_docx: { allowed: true, visible: true, message: 'Allowed' },
									view_placeholders: { allowed: true, visible: true, message: 'Allowed' },
								},
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-bundle-std"]').click();
		await page.locator('[data-testid="std-library-tab-bundle-preview"]').click();
		await expect(page.locator('[data-testid="std-library-bundle-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-bundle-status-bar"]')).toContainText('Preview status');
		await expect(page.locator('[data-testid="std-bundle-outline"]')).toContainText(
			'Invitation to Tender',
		);
		await expect(page.locator('[data-testid="std-bundle-preview-pane"]')).toContainText(
			'qualified tenderers',
		);
		await expect(page.locator('[data-testid="std-bundle-placeholder-panel"]')).toContainText(
			'Tender Identity',
		);
		await expect(page.locator('[data-testid="std-bundle-generate-preview"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-bundle-download-pdf"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-bundle-download-docx"]')).toBeVisible();
		await page.locator('[data-testid="std-bundle-outline"]').locator('button').nth(1).click();
		await expect(page.locator('[data-testid="std-bundle-preview-pane"]')).toContainText(
			'Operational instructions',
		);
		await expect(page.locator('[data-testid="std-library-bundle-tab"]')).not.toContainText('raw json');
		await expect(page.locator('[data-testid="std-library-bundle-tab"]')).not.toContainText('<xml');
	});

	test('usage tab renders read-only usage sections and excludes mutation actions', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'USAGE-STD',
								title: 'Usage STD',
								revision_label: 'Rev 3',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Passed',
								bundle_preview_status: 'Available',
								used_by_tender_count: 2,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Usage STD',
							version_code: 'USAGE-STD',
							revision_label: 'Rev 3',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: {
								identity: {
									title: 'Usage STD',
									revision: 'Rev 3',
									authority: 'PPRA',
									template_family: 'STD-WORKS',
								},
								source_evidence: {
									source_document: 'DOC-USAGE',
									source_file: 'Available',
									source_hash: 'Available',
									evidence_status: 'Registered',
								},
								supported_use: {
									category: 'Works',
									methods: ['Open Tender'],
									contract_type: 'Admeasurement / Unit Rate',
									requires_boq: 'Yes',
								},
								health_summary: {
									validation: 'Passed',
									bundle_preview: 'Available',
									generated_models: 'Available',
								},
								output_summary: {
									line: 'Structured template outputs are ready for controlled tender assembly.',
								},
								next_action: {
									status: 'Active',
									action: 'Preview bundle or create new revision.',
								},
							},
							validation: {
								overall_status: 'Passed',
								severity: 'Low',
								categories: [{ category: 'Structure Integrity', state: 'Passed' }],
								issues: [],
								remediation: 'No immediate remediation required.',
							},
							bundle_preview: {
								status_bar: {
									preview_status: 'Available',
									last_generated: '2026-05-08 16:00',
									output_type: 'Template-level preview',
									placeholder_count: 48,
									render_warnings: 0,
								},
								outline: ['Invitation to Tender'],
								preview_blocks: [{ section: 'Invitation to Tender', content: 'Preview' }],
								placeholders: [],
								actions: {
									generate_preview: { allowed: true, visible: true, message: 'Allowed' },
									download_pdf: { allowed: true, visible: true, message: 'Allowed' },
									download_docx: { allowed: true, visible: true, message: 'Allowed' },
									view_placeholders: { allowed: true, visible: true, message: 'Allowed' },
								},
							},
							usage: {
								summary: { tenders_using_count: 1 },
								tenders: [
									{
										code: 'TND-1001',
										title: 'Roads Rehabilitation Works FY 2026',
										status: 'Published',
										procuring_entity: 'KenTender Authority',
										view_label: 'View Tender',
									},
								],
								instances: [
									{
										code: 'INST-1001',
										status: 'In Use',
										publication_state: 'Published',
										view_label: 'View STD Instance Read-Only',
									},
								],
								outputs: [{ output_code: 'BNDL-1001', version: 'v1', view_label: 'View Evidence' }],
								addenda: [
									{
										addendum_code: 'ADD-001',
										linked_context: 'Clarification on qualification criteria',
										view_label: 'View Evidence',
									},
								],
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-usage-std"]').click();
		await page.locator('[data-testid="std-library-tab-usage"]').click();
		await expect(page.locator('[data-testid="std-library-usage-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-usage-summary"]')).toContainText('Tenders using this STD');
		await expect(page.locator('[data-testid="std-usage-tender-list"]')).toContainText('View Tender');
		await expect(page.locator('[data-testid="std-usage-instance-list"]')).toContainText(
			'View STD Instance Read-Only',
		);
		await expect(page.locator('[data-testid="std-usage-output-list"]')).toContainText('View Evidence');
		await expect(page.locator('[data-testid="std-usage-addendum-list"]')).toContainText('ADD-001');
		await expect(page.locator('[data-testid="std-library-usage-tab"]')).not.toContainText(
			'Create STD Instance',
		);
		await expect(page.locator('[data-testid="std-library-usage-tab"]')).not.toContainText(
			'Edit STD Instance',
		);
		await expect(page.locator('[data-testid="std-library-usage-tab"]')).not.toContainText(
			'Configure Tender Document',
		);
	});

	test('supersession tab shows lineage, tender impact, and create-new-revision safety', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'SUP-STD',
								title: 'Supersession STD',
								revision_label: 'Rev 7',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Passed',
								bundle_preview_status: 'Available',
								used_by_tender_count: 3,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Supersession STD',
							version_code: 'SUP-STD',
							revision_label: 'Rev 7',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: { identity: {}, source_evidence: {}, supported_use: {}, health_summary: {}, output_summary: {}, next_action: {} },
							validation: { overall_status: 'Passed', severity: 'Low', categories: [], issues: [], remediation: '' },
							bundle_preview: { status_bar: {}, outline: [], preview_blocks: [], placeholders: [], actions: {} },
							usage: { summary: { tenders_using_count: 0 }, tenders: [], instances: [], outputs: [], addenda: [] },
							supersession: {
								lineage: {
									current_version: 'SUP-STD',
									supersedes: 'SUP-STD-PREV',
									superseded_by: '',
									reason: 'PPRA correction',
									effective_date: 'Pending new revision',
								},
								impact: {
									existing_tender_impact:
										'Existing published tenders remain bound to the STD version used at publication unless a formal addendum or supersession process applies.',
									new_tenders_impact:
										'New tenders must use the newest approved version once supersession is effective.',
								},
								principle_text:
									'Existing published tenders remain bound to the STD version used at publication unless a formal addendum or supersession process applies.',
								actions: {
									create_new_revision: {
										label: 'Create New Revision',
										allowed: true,
										message: 'Allowed',
									},
									view_previous_version: { allowed: true, message: 'Allowed' },
									view_superseding_version: {
										allowed: false,
										message: 'Unavailable: no superseding version linked.',
									},
								},
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-sup-std"]').click();
		await page.locator('[data-testid="std-library-tab-supersession"]').click();
		await expect(page.locator('[data-testid="std-library-supersession-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-supersession-lineage"]')).toContainText('SUP-STD');
		await expect(page.locator('[data-testid="std-supersession-existing-tender-impact"]')).toContainText(
			'Existing published tenders remain bound',
		);
		await expect(page.locator('[data-testid="std-supersession-create-revision"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-supersession-tab"]')).not.toContainText(
			'Edit Active Version',
		);
	});

	test('advanced tab renders shell selectors and raw package stays collapsed by default', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'ADV-STD',
								title: 'Advanced STD',
								revision_label: 'Rev 8',
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
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Advanced STD',
							version_code: 'ADV-STD',
							revision_label: 'Rev 8',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: { identity: {}, source_evidence: {}, supported_use: {}, health_summary: {}, output_summary: {}, next_action: {} },
							validation: { overall_status: 'Passed', severity: 'Low', categories: [], issues: [], remediation: '' },
							bundle_preview: { status_bar: {}, outline: [], preview_blocks: [], placeholders: [], actions: {} },
							usage: { summary: { tenders_using_count: 0 }, tenders: [], instances: [], outputs: [], addenda: [] },
							supersession: { lineage: {}, impact: {}, actions: {} },
							advanced: {
								intro_text:
									'Advanced Technical View is for reviewing structured sections, parameters, forms, BOQ rules, source mappings, readiness rules, and generated model definitions. Most STD administration tasks can be completed from Summary, Validation, and Bundle Preview.',
								sections: [
									{ key: 'sections_clauses', label: 'Sections and Clauses' },
									{ key: 'parameters', label: 'Parameters' },
									{ key: 'forms', label: 'Forms' },
									{ key: 'boq_rules', label: 'Works / BOQ Rules' },
									{ key: 'source_mappings', label: 'Source Mappings' },
									{ key: 'readiness_rules', label: 'Readiness Rules' },
									{ key: 'generated_models', label: 'Generated Model Definitions' },
									{ key: 'raw_package_data', label: 'Raw Package Data' },
								],
								raw_package: {
									collapsed_by_default: true,
									technical_label: 'Technical (Read-Only)',
									read_only: true,
									visible_for_advanced_users: true,
								},
								editing: {
									enabled: false,
									reason: 'Editing is disabled for Active versions.',
								},
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-adv-std"]').click();
		await page.locator('[data-testid="std-library-tab-advanced"]').click();
		await expect(page.locator('[data-testid="std-advanced-technical-view"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-advanced-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-readonly-banner"]')).toContainText(
			'Editing is disabled for Active versions.',
		);
		await expect(page.locator('[data-testid="std-advanced-technical-view-toggle"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-sections-clauses"]')).toBeHidden();
		await page.locator('[data-testid="std-advanced-technical-view-toggle"]').click();
		await expect(page.locator('[data-testid="std-advanced-intro"]')).toContainText(
			'Most STD administration tasks can be completed from Summary, Validation, and Bundle Preview.',
		);
		await expect(page.locator('[data-testid="std-advanced-sections-clauses"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-parameters"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-forms"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-boq-rules"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-source-mappings"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-readiness-rules"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-generated-models"]')).toBeVisible();
		const rawBlock = page.locator('[data-testid="std-advanced-raw-package-data"]');
		await expect(rawBlock).toBeVisible();
		await expect(rawBlock).not.toHaveAttribute('open', '');
	});

	test('advanced source mappings shows plain labels and missing-row blocker routes to validation', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'MAP-STD',
								title: 'Mappings STD',
								revision_label: 'Rev 9',
								status: 'Active',
								procurement_category: 'Works',
								supported_methods: ['Open Tender'],
								source_authority: 'PPRA',
								validation_status: 'Blocked',
								bundle_preview_status: 'Available',
								used_by_tender_count: 0,
								supersession_status: 'Current',
								action_availability: {
									view_details: { allowed: true, message: 'Allowed' },
									preview_bundle: { allowed: true, message: 'Allowed' },
									validate: { allowed: true, message: 'Allowed' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Mappings STD',
							version_code: 'MAP-STD',
							revision_label: 'Rev 9',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Blocked',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: { identity: {}, source_evidence: {}, supported_use: {}, health_summary: {}, output_summary: {}, next_action: {} },
							validation: {
								overall_status: 'Blocked',
								severity: 'High',
								categories: [{ category: 'Source Mappings', state: 'Blocked' }],
								issues: ['Source mapping entry is missing for opening register schema.'],
								remediation: 'Resolve mapping blockers.',
							},
							bundle_preview: { status_bar: {}, outline: [], preview_blocks: [], placeholders: [], actions: {} },
							usage: { summary: { tenders_using_count: 0 }, tenders: [], instances: [], outputs: [], addenda: [] },
							supersession: { lineage: {}, impact: {}, actions: {} },
							advanced: {
								intro_text:
									'Advanced Technical View is for reviewing structured sections, parameters, forms, BOQ rules, source mappings, readiness rules, and generated model definitions. Most STD administration tasks can be completed from Summary, Validation, and Bundle Preview.',
								sections: [
									{ key: 'sections_clauses', label: 'Sections and Clauses' },
									{ key: 'parameters', label: 'Parameters' },
									{ key: 'forms', label: 'Forms' },
									{ key: 'boq_rules', label: 'Works / BOQ Rules' },
									{ key: 'source_mappings', label: 'Source Mappings' },
									{ key: 'readiness_rules', label: 'Readiness Rules' },
									{ key: 'generated_models', label: 'Generated Model Definitions' },
									{ key: 'raw_package_data', label: 'Raw Package Data' },
								],
								raw_package: {
									collapsed_by_default: true,
									technical_label: 'Technical (Read-Only)',
									read_only: true,
									visible_for_advanced_users: true,
								},
								editing: {
									enabled: false,
									reason: 'Editing is disabled for Active versions.',
								},
								source_mappings: {
									targets: [
										{ code: 'DSM', label: 'Submission Requirements (DSM)' },
										{ code: 'DOM', label: 'Opening Register (DOM)' },
										{ code: 'DEM', label: 'Evaluation Rules (DEM)' },
										{ code: 'DCM', label: 'Contract Carry-Forward (DCM)' },
										{ code: 'BUNDLE', label: 'Tender Document Bundle' },
									],
									rows: [
										{
											source: 'Tender Data Sheet - Submission Deadline',
											target_code: 'DSM',
											target_label: 'Submission Requirements (DSM)',
											generated_element: 'submission_requirements.deadline',
											mandatory: 'Yes',
											status: 'Valid',
											last_validated: '2026-05-08 17:00',
										},
										{
											source: 'Opening Procedure - Register Format',
											target_code: 'DOM',
											target_label: 'Opening Register (DOM)',
											generated_element: 'opening_register.schema',
											mandatory: 'Yes',
											status: 'Missing',
											last_validated: '2026-05-08 17:00',
											validation_blocker: {
												tab: 'validation',
												reason:
													'Source mapping entry is missing for opening register schema.',
											},
										},
									],
									read_only: true,
								},
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-map-std"]').click();
		await page.locator('[data-testid="std-library-tab-advanced"]').click();
		await page.locator('[data-testid="std-advanced-technical-view-toggle"]').click();
		const sourceMappings = page.locator('[data-testid="std-advanced-source-mappings"]');
		await expect(sourceMappings).toContainText('Submission Requirements (DSM)');
		await expect(sourceMappings).toContainText('Opening Register (DOM)');
		await expect(sourceMappings).toContainText('Evaluation Rules (DEM)');
		await expect(sourceMappings).toContainText('Contract Carry-Forward (DCM)');
		await expect(sourceMappings).toContainText('Tender Document Bundle');
		await expect(sourceMappings).toContainText('Generated Element');
		await expect(sourceMappings).toContainText('Read-only mapping surface');
		await sourceMappings.locator('.std-advanced-mapping-blocker').first().click();
		await expect(page.locator('[data-testid="std-library-validation-tab"]')).toBeVisible();
	});

	test('audit tab renders read-only event table with denied entries and no mutation controls', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		await page.route('**/api/method/**get_std_library_templates*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						rows: [],
						items: [
							{
								version_code: 'AUD-STD',
								title: 'Audit STD',
								revision_label: 'Rev 10',
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
									validate: { allowed: false, message: 'Unavailable' },
									submit_for_review: { allowed: false, message: 'Unavailable' },
									new_revision: { allowed: true, message: 'Allowed' },
									view_usage: { allowed: true, message: 'Allowed' },
								},
							},
						],
						total_count: 1,
					},
				}),
			});
		});
		await page.route('**/api/method/**get_std_library_template_detail*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						detail: {
							title: 'Audit STD',
							version_code: 'AUD-STD',
							revision_label: 'Rev 10',
							status: 'Active',
							authority: 'PPRA',
							validation_status: 'Passed',
							bundle_preview_status: 'Available',
							state_banner:
								'This STD version is active and immutable. Create a new revision to make changes.',
							summary: { identity: {}, source_evidence: {}, supported_use: {}, health_summary: {}, output_summary: {}, next_action: {} },
							validation: { overall_status: 'Passed', severity: 'Low', categories: [], issues: [], remediation: '' },
							bundle_preview: { status_bar: {}, outline: [], preview_blocks: [], placeholders: [], actions: {} },
							usage: { summary: { tenders_using_count: 0 }, tenders: [], instances: [], outputs: [], addenda: [] },
							supersession: { lineage: {}, impact: {}, actions: {} },
							advanced: { intro_text: '', sections: [], raw_package: {}, editing: {} },
							audit: {
								read_only: true,
								denied_visible: true,
								rows: [
									{
										timestamp: '2026-05-08 16:45',
										actor: 'Administrator',
										event: 'Package Imported',
										object: 'AUD-STD',
										result: 'Success',
										reason: 'Structured package accepted.',
										audit_code: 'STD_TEMPLATE_IMPORTED',
									},
									{
										timestamp: '2026-05-08 16:50',
										actor: 'System Manager',
										event: 'Mutation Attempt Blocked',
										object: 'AUD-STD',
										result: 'Denied',
										reason: 'Active version is immutable.',
										audit_code: 'STD_TEMPLATE_MUTATION_BLOCKED',
									},
								],
							},
						},
					},
				}),
			});
		});

		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-aud-std"]').click();
		await page.locator('[data-testid="std-library-tab-audit"]').click();
		await expect(page.locator('[data-testid="std-library-audit-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-audit-event-table"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-audit-event-row"]')).toHaveCount(2);
		await expect(page.locator('[data-testid="std-library-audit-tab"]')).toContainText('Denied');
		await expect(page.locator('[data-testid="std-library-audit-tab"]')).toContainText('read-only');
		await expect(page.locator('[data-testid="std-library-audit-tab"]')).not.toContainText(
			'Create STD Instance',
		);
		await expect(page.locator('[data-testid="std-library-audit-tab"]')).not.toContainText(
			'Edit STD Instance',
		);
	});

	test('launcher/sidebar click path opens STD library shell', async ({ page }) => {
		await loginAsAdministrator(page);
		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Official STD Library');
		await dismissOptionalDeskModals(page);
		await expect(page.locator('[data-testid="std-library-page"]')).toBeVisible({ timeout: 90_000 });
		await expect(page).toHaveURL(/std-engine\/library|std-engine/i);
	});
});
