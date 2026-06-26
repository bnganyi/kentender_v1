/**
 * P3-001 — Root route opens PP3 Workbench surface.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

test.describe('P3-001 Workbench route', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('root route renders PP4 Workbench with high-fidelity regions', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp4-workbench')).toHaveCount(1);
		await expect(page.getByTestId('pp4-topbar')).toBeVisible();
		await expect(page.getByTestId('pp4-breadcrumbs')).toBeVisible();
		await expect(page.getByTestId('pp4-stats-grid')).toBeVisible();
		await expect(page.getByTestId('pp4-work-queue-tabs')).toBeVisible();
		await expect(page.getByTestId('pp4-package-grid')).toBeVisible();
		await expect(page.getByTestId('pp4-create-package-card')).toBeVisible();
		await expect(page.getByTestId('pp4-topbar-search')).toBeVisible();
		await expect(page.getByText('End-to-End Procurement Planning')).toBeVisible();
		await expect(page.getByText('PKG-MOH-2026-001')).toBeVisible();

		await page.screenshot({ path: 'artifacts/p3-001-workbench-route.png', fullPage: true });
	});

	test('PP4 tab badges load live workbench queue counts', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: {
								draft_packages: 2,
								needs_review: 5,
								ready_to_release: 7,
								needs_planning: 11,
								blocked: 1,
								recently_released: 3,
							},
						},
					}),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp4-count-in-creation')).toHaveText('2');
		await expect(page.getByTestId('pp4-count-awaiting-review')).toHaveText('5');
		await expect(page.getByTestId('pp4-count-ready-for-release')).toHaveText('7');
		await expect(page.getByTestId('pp4-count-all-packages')).toHaveText('14');
	});

	test('PP4 KPI cards load live backend values', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.landing.get_pp_landing_shell_data',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							kpis: [
								{ id: 'total_packages', value: 8, format: 'int' },
								{ id: 'total_planned_value', value: 1200000000, format: 'currency', currency: 'KES' },
								{ id: 'approved_packages', value: 5, format: 'int' },
								{ id: 'ready_for_tender', value: 3, format: 'int' },
							],
						},
					}),
				});
			}
		);
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: {
								draft_packages: 2,
								needs_review: 5,
								ready_to_release: 7,
							},
						},
					}),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp4-kpi-total-estimate-value')).toHaveText('KES 1.2B');
		await expect(page.getByTestId('pp4-kpi-active-packages-value')).toHaveText('14');
		await expect(page.getByTestId('pp4-kpi-approval-rate-value')).toHaveText('57%');
		await expect(page.getByTestId('pp4-kpi-pending-action-value')).toHaveText('12 Items');
	});

	test('PP4 selected tab loads package list for that queue', async ({ page }) => {
		const requestedQueues: string[] = [];
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: {
								draft_packages: 1,
								needs_review: 1,
								ready_to_release: 1,
							},
						},
					}),
				});
			}
		);

		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model',
			async (route) => {
				const req = route.request();
				const body = req.postData() || '';
				const decoded = decodeURIComponent(body);
				let queue = 'draft_packages';
				if (body.includes('queue=needs_review') || decoded.includes('"queue":"needs_review"')) {
					queue = 'needs_review';
				}
				if (body.includes('queue=ready_release') || decoded.includes('"queue":"ready_release"')) {
					queue = 'ready_release';
				}
				requestedQueues.push(queue);

				const byQueue: Record<string, unknown[]> = {
					draft_packages: [
						{
							title: 'Draft Package One',
							underlying_object_code: 'PKG-DRF-001',
							status_pill_label: 'Draft',
							state_label: 'Draft package',
							package_description: 'Draft package custom description',
							consolidated_demand_count: 5,
							status_detail: 'Draft package detail',
							meta_line: 'Open Tender · KES 100,000',
							primary_action: { label: 'Complete Package' },
						},
					],
					needs_review: [
						{
							title: 'Review Package One',
							underlying_object_code: 'PKG-REV-001',
							status_pill_label: 'In Review',
							state_label: 'Needs review',
							package_description: 'Needs review custom description',
							consolidated_demand_count: 18,
							status_detail: 'Needs review detail',
							meta_line: 'RFP · KES 200,000',
							primary_action: { label: 'Review Package' },
						},
					],
					ready_release: [
						{
							title: 'Release Package One',
							underlying_object_code: 'PKG-RDY-001',
							status_pill_label: 'Ready for Release',
							state_label: 'Ready to release',
							package_description: 'Ready for release custom description',
							consolidated_demand_count: 42,
							status_detail: 'Ready to release detail',
							meta_line: 'Open Tender · KES 300,000',
							primary_action: { label: 'Release to Tender' },
						},
					],
				};

				const items = byQueue[queue] || [];
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							queue,
							total: items.length,
							items,
						},
					}),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByText('PKG-DRF-001')).toBeVisible();
		await expect(page.getByText('PKG-REV-001')).toBeVisible();
		await expect(page.getByText('PKG-RDY-001')).toBeVisible();
		await expect(page.getByText('Draft package custom description')).toBeVisible();
		await expect(page.locator('text=CONSOLIDATED').first()).toBeVisible();
		await expect(page.getByText('5 Demands')).toBeVisible();
		await expect(page.getByText('Next package action:')).toHaveCount(0);
		await expect(page.getByText('15% Progress')).toBeVisible();
		await expect(page.getByText('65% Progress')).toBeVisible();
		await expect(page.getByText('100% Complete')).toBeVisible();

		await page.getByTestId('pp4-tab-awaiting-review').click();
		await expect(page.getByText('PKG-REV-001')).toBeVisible();
		await expect(page.getByText('65% Progress')).toBeVisible();

		await page.getByTestId('pp4-tab-ready-for-release').click();
		await expect(page.getByText('PKG-RDY-001')).toBeVisible();
		await expect(page.getByText('100% Complete')).toBeVisible();
		expect(requestedQueues).toContain('needs_review');
		expect(requestedQueues).toContain('ready_release');
	});

	test('PP4 search filters visible package cards', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: { draft_packages: 2, needs_review: 0, ready_to_release: 0 },
						},
					}),
				});
			}
		);
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model',
			async (route) => {
				const req = route.request();
				const body = decodeURIComponent(req.postData() || '');
				const queue = body.includes('"queue":"needs_review"') ? 'needs_review' : 'draft_packages';
				const items =
					queue === 'draft_packages'
						? [
								{
									title: 'Medical Supplies Q1',
									underlying_object_code: 'PKG-MOH-2026-001',
									status_pill_label: 'Draft',
									state_label: 'Draft package',
									package_description: 'Consolidated medicine purchases',
									consolidated_demand_count: 42,
									meta_line: 'Open Tender · KES 450,000,000',
									primary_action: { label: 'Complete Package' },
								},
								{
									title: 'Hospital Equipment Upgrade',
									underlying_object_code: 'PKG-MOH-2026-002',
									status_pill_label: 'Draft',
									state_label: 'Draft package',
									package_description: 'MRI scanner and related equipment',
									consolidated_demand_count: 18,
									meta_line: 'Open Tender · KES 320,500,000',
									primary_action: { label: 'Complete Package' },
								},
							]
						: [];
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({ message: { ok: true, queue, total: items.length, items } }),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const searchInput = page.getByTestId('pp4-search-input');
		await expect(searchInput).toBeVisible();
		await expect(page.getByText('PKG-MOH-2026-001')).toBeVisible();
		await expect(page.getByText('PKG-MOH-2026-002')).toBeVisible();

		await searchInput.fill('MRI');
		await expect(page.getByText('PKG-MOH-2026-001')).toHaveCount(0);
		await expect(page.getByText('PKG-MOH-2026-002')).toBeVisible();

		await searchInput.fill('non-existent package');
		await expect(page.getByText('No packages found')).toBeVisible();
	});

	test('PP4 filter drawer applies staged filters and clear-all resets', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: { draft_packages: 1, needs_review: 1, ready_to_release: 1 },
						},
					}),
				});
			}
		);
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model',
			async (route) => {
				const req = route.request();
				const body = decodeURIComponent(req.postData() || '');
				const queue = body.includes('queue=needs_review') || body.includes('"queue":"needs_review"')
					? 'needs_review'
					: body.includes('queue=ready_release') || body.includes('"queue":"ready_release"')
						? 'ready_release'
						: 'draft_packages';
				const byQueue: Record<string, unknown[]> = {
					draft_packages: [
						{
							title: 'Package A',
							underlying_object_code: 'PKG-FLT-001',
							status_pill_label: 'Draft',
							state_label: 'Draft package',
							package_description: 'Lower value draft package',
							consolidated_demand_count: 5,
							meta_line: 'Open Tender · KES 100,000',
							department_label: 'IT Infrastructure',
							created_on: '2026-06-10',
							primary_action: { label: 'Complete Package' },
						},
					],
					needs_review: [
						{
							title: 'Package B',
							underlying_object_code: 'PKG-FLT-002',
							status_pill_label: 'In Review',
							state_label: 'Needs review',
							package_description: 'Mid value review package',
							consolidated_demand_count: 12,
							meta_line: 'Open Tender · KES 200,000',
							department_label: 'Ministry of Health (MOH)',
							created_on: '2026-06-18',
							primary_action: { label: 'Review Package' },
						},
					],
					ready_release: [
						{
							title: 'Package C',
							underlying_object_code: 'PKG-FLT-003',
							status_pill_label: 'Ready for Release',
							state_label: 'Ready to release',
							package_description: 'Higher value release package',
							consolidated_demand_count: 18,
							meta_line: 'Open Tender · KES 300,000',
							department_label: 'Facilities Management',
							created_on: '2026-06-22',
							primary_action: { label: 'Release to Tender' },
						},
					],
				};
				const items = byQueue[queue] || [];
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({ message: { ok: true, queue, total: items.length, items } }),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByText('PKG-FLT-001')).toBeVisible();
		await expect(page.getByText('PKG-FLT-002')).toBeVisible();
		await expect(page.getByText('PKG-FLT-003')).toBeVisible();

		await page.getByTestId('pp4-filters').click();
		await expect(page.getByTestId('pp4-filter-backdrop')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-drawer')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-search')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-status-in-creation')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-status-awaiting-review')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-status-ready-for-release')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-department')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-value-range-kes-100m-500m')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-created-from')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-created-to')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-apply')).toBeVisible();
		await expect(page.getByTestId('pp4-filter-clear-all')).toBeVisible();

		await page.getByTestId('pp4-filter-status-awaiting-review').click();
		await expect(page.getByText('PKG-FLT-001')).toBeVisible();
		await expect(page.getByText('PKG-FLT-002')).toBeVisible();
		await expect(page.getByText('PKG-FLT-003')).toBeVisible();

		await page.getByTestId('pp4-filter-apply').click();
		await expect(page.getByText('PKG-FLT-002')).toBeVisible();
		await expect(page.getByText('PKG-FLT-001')).toHaveCount(0);
		await expect(page.getByText('PKG-FLT-003')).toHaveCount(0);
		await expect(page.getByTestId('pp4-count-all-packages')).toHaveText('1');
		await expect(page.getByTestId('pp4-count-in-creation')).toHaveText('0');
		await expect(page.getByTestId('pp4-count-awaiting-review')).toHaveText('1');
		await expect(page.getByTestId('pp4-count-ready-for-release')).toHaveText('0');

		await page.getByTestId('pp4-filters').click();
		await page.getByTestId('pp4-filter-clear-all').click();
		await expect(page.getByText('PKG-FLT-001')).toBeVisible();
		await expect(page.getByText('PKG-FLT-002')).toBeVisible();
		await expect(page.getByText('PKG-FLT-003')).toBeVisible();
		await expect(page.getByTestId('pp4-count-all-packages')).toHaveText('3');
		await expect(page.getByTestId('pp4-count-in-creation')).toHaveText('1');
		await expect(page.getByTestId('pp4-count-awaiting-review')).toHaveText('1');
		await expect(page.getByTestId('pp4-count-ready-for-release')).toHaveText('1');
	});

	test('PP4 sort menu selects explicit mode and reorders cards', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: { draft_packages: 1, needs_review: 1, ready_to_release: 1 },
						},
					}),
				});
			}
		);
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model',
			async (route) => {
				const req = route.request();
				const body = decodeURIComponent(req.postData() || '');
				const queue = body.includes('queue=needs_review') || body.includes('"queue":"needs_review"')
					? 'needs_review'
					: body.includes('queue=ready_release') || body.includes('"queue":"ready_release"')
						? 'ready_release'
						: 'draft_packages';
				const byQueue: Record<string, unknown[]> = {
					draft_packages: [
						{
							title: 'Package A',
							underlying_object_code: 'PKG-SORT-001',
							status_pill_label: 'Draft',
							state_label: 'Draft package',
							package_description: 'Lower value draft package',
							consolidated_demand_count: 5,
							meta_line: 'Open Tender · KES 100,000',
							primary_action: { label: 'Complete Package' },
						},
					],
					needs_review: [
						{
							title: 'Package B',
							underlying_object_code: 'PKG-SORT-002',
							status_pill_label: 'In Review',
							state_label: 'Needs review',
							package_description: 'Mid value review package',
							consolidated_demand_count: 12,
							meta_line: 'Open Tender · KES 200,000',
							primary_action: { label: 'Review Package' },
						},
					],
					ready_release: [
						{
							title: 'Package C',
							underlying_object_code: 'PKG-SORT-003',
							status_pill_label: 'Ready for Release',
							state_label: 'Ready to release',
							package_description: 'Higher value release package',
							consolidated_demand_count: 18,
							meta_line: 'Open Tender · KES 300,000',
							primary_action: { label: 'Release to Tender' },
						},
					],
				};
				const items = byQueue[queue] || [];
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({ message: { ok: true, queue, total: items.length, items } }),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await page.getByTestId('pp4-sort').click();
		await expect(page.getByTestId('pp4-sort-menu')).toBeVisible();
		await page.getByTestId('pp4-sort-option-value-high-low').click();
		await expect(page.getByTestId('pp4-sort-label')).toHaveText('Sort: Value High-Low');
		await expect(page.locator('[data-testid="pp4-package-card"]').first().getByTestId('pp4-package-code')).toHaveText(
			'PKG-SORT-003'
		);
		await page.getByTestId('pp4-filters').click();
		await page.getByTestId('pp4-filter-clear-all').click();
		await page.getByTestId('pp4-sort').click();
		await page.getByTestId('pp4-sort-option-newest').click();
		await expect(page.getByTestId('pp4-sort-label')).toHaveText('Sort: Newest');
	});

	test('PP4 primary card action opens package route', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: { draft_packages: 1, needs_review: 0, ready_to_release: 0 },
						},
					}),
				});
			}
		);
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model',
			async (route) => {
				const req = route.request();
				const body = decodeURIComponent(req.postData() || '');
				const queue = body.includes('"queue":"needs_review"') ? 'needs_review' : 'draft_packages';
				const items =
					queue === 'draft_packages'
						? [
								{
									title: 'Review Target Package',
									underlying_object_code: 'PKG-ACT-001',
									status_pill_label: 'Draft',
									state_label: 'Draft package',
									package_description: 'Action wiring test description',
									consolidated_demand_count: 3,
									meta_line: 'RFP · KES 210,000',
									primary_action: { label: 'Complete Package', action: 'complete_package', target: 'PKG-ACT-001' },
									secondary_actions: [{ label: 'View Package', action: 'view_package', target: 'PKG-ACT-001' }],
								},
							]
						: [];
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({ message: { ok: true, queue, total: items.length, items } }),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByText('PKG-ACT-001')).toBeVisible();
		await page
			.locator('[data-testid="pp4-package-card"]', { hasText: 'PKG-ACT-001' })
			.getByTestId('pp4-package-primary-action')
			.click();
		await expect(page).toHaveURL(/package_code=PKG-ACT-001/);
	});

	test('PP4 secondary card action opens package route', async ({ page }) => {
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_queue_counts.get_pp_workbench_queue_counts',
			async (route) => {
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({
						message: {
							ok: true,
							counts: { draft_packages: 1, needs_review: 0, ready_to_release: 0 },
						},
					}),
				});
			}
		);
		await page.route(
			'**/api/method/kentender_procurement.procurement_planning.api.workbench_item.get_pp_workbench_item_view_model',
			async (route) => {
				const req = route.request();
				const body = decodeURIComponent(req.postData() || '');
				const queue = body.includes('"queue":"needs_review"') ? 'needs_review' : 'draft_packages';
				const items =
					queue === 'draft_packages'
						? [
								{
									title: 'Secondary Target Package',
									underlying_object_code: 'PKG-SEC-001',
									status_pill_label: 'Draft',
									state_label: 'Draft package',
									package_description: 'Secondary action wiring test',
									consolidated_demand_count: 2,
									meta_line: 'Open Tender · KES 120,000',
									primary_action: { label: 'Complete Package', action: 'complete_package', target: 'PKG-SEC-001' },
									secondary_actions: [{ label: 'View Package', action: 'view_package', target: 'PKG-SEC-001' }],
								},
							]
						: [];
				await route.fulfill({
					status: 200,
					contentType: 'application/json',
					body: JSON.stringify({ message: { ok: true, queue, total: items.length, items } }),
				});
			}
		);

		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByText('PKG-SEC-001')).toBeVisible();
		await page
			.locator('[data-testid="pp4-package-card"]', { hasText: 'PKG-SEC-001' })
			.getByTestId('pp4-package-secondary-action')
			.click();
		await expect(page).toHaveURL(/package_code=PKG-SEC-001/);
	});
});
