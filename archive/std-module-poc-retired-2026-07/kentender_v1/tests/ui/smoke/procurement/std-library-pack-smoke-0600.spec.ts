/**
 * STD-LIB-0600 — Official STD Library UI smoke tests (pack doc 2 §26).
 * Pack checklist + acceptance: no "Create STD Instance"; title "Official STD Library";
 * Bundle Preview tab present; Advanced not default tab.
 */
import type { Page } from '@playwright/test';
import { expect, test } from '@playwright/test';

import { loginAsAdministrator, loginAsProcurementOfficer } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

const VC_DOC1 = 'PPRA-WORKS-DOC1-2022';

/** Routes required for the full import wizard flow through Step 6 (matches std-library-shell import test). */
async function routePack0600ImportWizard(page: Page) {
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
									label:
										'PPRA Works — Building and Associated Civil Engineering Works — Rev April 2022',
								},
							],
						},
						{ value: 'UPLOADED_STRUCTURED_PACKAGE', label: 'Uploaded Structured Package', entries: [] },
						{ value: 'CONNECTED_REGISTRY', label: 'Connected Registry', entries: [] },
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
		await new Promise((resolve) => setTimeout(resolve, 200));
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
						mapping_coverage: { bundle: 12, submission: 10, opening: 8, evaluation: 14, contract: 9 },
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
						warnings: [],
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
						submit: 'legal or policy review',
						activate: 'activate',
					},
				},
			}),
		});
	});
}

test.describe('STD-LIB-0600 — pack §26 Official STD Library smoke', () => {
	test.describe.configure({ mode: 'serial' });
	test.setTimeout(240_000);

	test('§26 items 1–16 — landing, forbidden strings, PPRA Works DOC1 card, detail tabs', async ({
		page,
		baseURL,
	}) => {
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
								version_code: VC_DOC1,
								title: 'PPRA Works — Building (DOC1 reference)',
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
							title: 'PPRA Works — Building (DOC1 reference)',
							version_code: VC_DOC1,
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
									last_generated: '2026-05-08 12:00',
									output_type: 'Template-level preview',
									placeholder_count: 12,
									render_warnings: 0,
								},
								outline: ['Invitation to Tender', 'Instructions to Tenderers'],
								preview_blocks: [
									{
										section: 'Invitation to Tender',
										content: 'Official invitation text for qualified tenderers.',
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
							usage: {
								summary: { tenders_using_count: 0 },
								tenders: [],
								instances: [],
								outputs: [],
								addenda: [],
							},
							supersession: {
								lineage: {
									current_version: VC_DOC1,
									supersedes: 'None',
									superseded_by: 'None',
									reason: '—',
									effective_date: '—',
								},
								impact: {
									existing_tender_impact:
										'Existing tenders retain their published bundle references.',
									new_tenders_impact: 'New tenders must use the current active version.',
								},
								actions: {
									create_new_revision: { allowed: true, message: 'Allowed' },
								},
							},
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
								source_mappings: { targets: [], rows: [] },
							},
							audit: {
								rows: [
									{
										timestamp: '2026-05-08 10:00',
										actor: 'System',
										event: 'Imported',
										object: VC_DOC1,
										result: 'Allowed',
										reason: '—',
										audit_code: 'STD_IMPORT',
									},
								],
							},
						},
					},
				}),
			});
		});

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(page.locator('[data-testid="std-library-header-title"]')).toHaveText(
			'Official STD Library',
		);
		await expect(shell.locator('[data-testid="std-library-import-package-button"]')).toHaveText(
			'Import Official STD Package',
		);
		await expect(shell).not.toContainText('Create STD Instance');
		await expect(shell).not.toContainText('Create Template Version');
		await expect(shell.locator('[data-testid="std-library-guidance-strip"]')).toContainText(
			'Official STDs are imported as structured packages',
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
		await expect(shell.locator('[data-testid="std-library-search-input"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-filter-button"]')).toBeVisible();

		await expect(
			page.locator('[data-testid="std-library-card-title-ppra-works-doc1-2022"]'),
		).toContainText('PPRA Works');
		await expect(page.locator('[data-testid="std-library-card-ppra-works-doc1-2022"]')).toContainText(
			/DOC1|DOC\s*1/i,
		);

		await page.locator('[data-testid="std-library-card-view-details-ppra-works-doc1-2022"]').click();
		await expect(page.locator('[data-testid="std-library-tab-summary"]')).toHaveClass(/is-active/);
		await expect(page.locator('[data-testid="std-library-tab-bundle-preview"]')).toBeVisible();

		await expect(page.locator('[data-testid="std-library-summary-source-evidence"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-supported-use"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-library-summary-source-evidence"]')).toContainText(
			'DOC1',
		);

		await page.locator('[data-testid="std-library-tab-validation"]').click();
		await expect(page.locator('[data-testid="std-library-validation-categories"]')).toBeVisible();

		await page.locator('[data-testid="std-library-tab-bundle-preview"]').click();
		await expect(page.locator('[data-testid="std-bundle-outline"]')).toBeVisible();

		await page.locator('[data-testid="std-library-tab-usage"]').click();
		const usageTab = page.locator('[data-testid="std-library-usage-tab"]');
		await expect(usageTab).toBeVisible();
		await expect(usageTab).not.toContainText('Create STD Instance');

		await page.locator('[data-testid="std-library-tab-supersession"]').click();
		await expect(page.locator('[data-testid="std-supersession-create-revision"]')).toBeVisible();

		await page.locator('[data-testid="std-library-tab-advanced"]').click();
		await expect(page.locator('[data-testid="std-library-advanced-tab"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-raw-package-data"]')).not.toHaveAttribute(
			'open',
			'',
		);

		await page.locator('[data-testid="std-library-tab-audit"]').click();
		await expect(page.locator('[data-testid="std-audit-event-table"]')).toBeVisible();

		await page.locator('[data-testid="std-library-tab-summary"]').click();
		await expect(page.locator('[data-testid="std-library-tab-summary"]')).toHaveClass(/is-active/);
	});

	test('§26 item 22 — Register Source warns registration does not activate STD', async ({
		page,
		baseURL,
	}) => {
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

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await page.locator('[data-testid="std-library-register-source-button"]').click();
		await expect(page.locator('[data-testid="std-register-source-warning"]')).toContainText(
			'does not make it available for tenders',
		);
		await page.locator('[data-testid="std-register-source-code"]').fill('SRC-DOC1');
		await page.locator('[data-testid="std-register-source-title"]').fill('PPRA Works DOC1 PDF');
		await page.locator('[data-testid="std-register-source-authority"]').fill('PPRA');
		await page.locator('[data-testid="std-register-source-revision"]').fill('Rev April 2022');
		await page.locator('[data-testid="std-register-source-save"]').click();
		await expect(page.locator('[data-testid="std-register-source-panel"]')).toContainText(
			'does not make an STD available for tenders',
		);
	});

	test('§26 items 17–21 — import wizard six steps, step 1 warning, step 3 structure, step 5 bundle', async ({
		page,
		baseURL,
	}) => {
		await routePack0600ImportWizard(page);

		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await page.locator('[data-testid="std-library-import-package-button"]').click();
		await expect(page).toHaveURL(/std-engine\/library\/import/i, { timeout: 90_000 });
		await expect(page.locator('[data-testid="std-package-import-page"]')).toBeVisible({
			timeout: 90_000,
		});
		await expect(page.locator('.std-package-import-step')).toHaveCount(6);
		await expect(page.locator('[data-testid="std-import-raw-file-warning"]')).toContainText(
			'Raw PDF, Word, or spreadsheet files',
		);

		await page.locator('[data-testid="std-import-package-source-select"]').selectOption(
			'BUILTIN_SEED_PACKAGE',
		);
		await page
			.locator('[data-testid="std-import-package-file-picker"]')
			.selectOption('PPRA-WORKS-BLDG-2022-04');
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'2. Confirm Source Evidence',
		);

		await page.locator('[data-testid="std-import-source-authority"]').fill('PPRA');
		await page.locator('[data-testid="std-import-source-title"]').fill('KE-PPRA-WORKS-BLDG-2022-04-POC');
		await page.locator('[data-testid="std-import-source-revision"]').fill('Rev April 2022');
		await page.locator('[data-testid="std-import-source-review-status"]').selectOption('Draft');
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'3. Review Detected Structure',
		);
		await expect(page.locator('[data-testid="std-import-detected-sections"]')).toContainText(
			'3 parts, 10 sections detected',
		);

		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'4. Validate Structured Model',
		);
		await page.locator('[data-testid="std-package-import-next"]').click();
		await expect(page.locator('.std-package-import-step.is-active')).toContainText(
			'5. Preview Tender Bundle',
		);
		await expect(page.locator('[data-testid="std-import-bundle-outline"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-import-placeholder-list"]')).toContainText(
			'To be completed during tender preparation',
		);

		await expect(page.locator('[data-testid="std-package-import-page"]')).not.toContainText(
			'Create STD Instance',
		);
	});

	test('§26 item 23 — Procurement Officer cannot access Official STD Library page shell', async ({
		page,
		baseURL,
	}) => {
		await loginAsProcurementOfficer(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		await expect(page.locator('[data-testid="std-library-page"]')).toHaveCount(0);
		await expect(page.locator('[data-testid="std-advanced-source-mappings"]')).toHaveCount(0);
	});
});
