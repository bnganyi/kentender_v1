/**
 * UI-HARD-1600 — STD Administrator UI smoke (pack §21 ticket 1600, doc §21.1).
 *
 * Test codes align with the Cursor pack `UI-SMOKE-STD-*` matrix.
 */
import type { Page } from '@playwright/test';
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('UI-HARD-1600 — UI-SMOKE-STD-* (STD Administrator)', () => {
	test.setTimeout(180_000);

	test('UI-SMOKE-STD-001 — STD Admin lands on Official STD Library', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page).toHaveURL(/std-engine\/library|library/i, { timeout: 90_000 });
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-header-title"]')).toHaveText('Official STD Library', {
			timeout: 30_000,
		});
	});

	test('UI-SMOKE-STD-002 — Import Official STD Package visible', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		const importBtn = shell.locator('[data-testid="std-library-import-package-button"]');
		await expect(importBtn).toBeVisible();
		await expect(importBtn).toHaveText('Import Official STD Package');
	});

	test('UI-SMOKE-STD-003 — Create STD Instance absent', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-create-instance-button-absent"]')).toBeAttached();
		await expect(shell).not.toContainText('Create STD Instance');
	});

	test('UI-SMOKE-STD-004 — Active template advanced edit disabled', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		await routeActiveAdvancedReadOnly(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await page.locator('[data-testid="std-library-card-view-details-adv-std"]').click();
		await page.locator('[data-testid="std-library-tab-advanced"]').click();
		await expect(page.locator('[data-testid="std-advanced-technical-view"]')).toBeVisible();
		await expect(page.locator('[data-testid="std-advanced-readonly-banner"]')).toContainText(
			'Editing is disabled for Active versions.',
		);
	});

	test('UI-SMOKE-STD-005 — Advanced Technical View hidden by default', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/std-engine/library`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const shell = page.locator('[data-testid="std-library-page"]');
		await expect(shell).toBeVisible({ timeout: 90_000 });
		await expect(shell.locator('[data-testid="std-library-advanced-view-toggle"]')).toBeVisible();
		await expect(shell.locator('[data-testid="std-library-advanced-catalogue-open"]')).toBeHidden();
	});
});

/** One-row list + detail so Advanced tab shows read-only banner (mirrors std-library-shell advanced tab test). */
async function routeActiveAdvancedReadOnly(page: Page) {
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
						summary: {
							identity: {},
							source_evidence: {},
							supported_use: {},
							health_summary: {},
							output_summary: {},
							next_action: {},
						},
						validation: { overall_status: 'Passed', severity: 'Low', categories: [], issues: [], remediation: '' },
						bundle_preview: { status_bar: {}, outline: [], preview_blocks: [], placeholders: [], actions: {} },
						usage: { summary: { tenders_using_count: 0 }, tenders: [], instances: [], outputs: [], addenda: [] },
						supersession: { lineage: {}, impact: {}, actions: {} },
						advanced: {
							intro_text: 'Advanced Technical View is for reviewing structured sections.',
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
}
