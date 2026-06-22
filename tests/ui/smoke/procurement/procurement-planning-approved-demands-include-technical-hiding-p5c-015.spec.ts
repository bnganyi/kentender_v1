/**
 * P5C-015 — Include-in-Plan technical hiding negative gate.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const APPROVED_DEMANDS_QUEUE_API =
	'**/api/method/**get_pp_approved_demands_awaiting_planning*';
const APPROVED_DEMAND_DRAWER_API =
	'**/api/method/**get_pp_approved_demand_planning_drawer*';
const INCLUDE_DEMAND_API =
	'**/api/method/**include_pp_demand_in_procurement_plan*';
const PLAN_SEARCH_API = '**/api/method/**search_procurement_plan*';

const FORBIDDEN_TECHNICAL_COPY = [
	/PLANINCL-MOH-2026-001/i,
	/PLANINCL-/i,
	/source object/i,
	/target object/i,
	/technical refs/i,
];

const READY_QUEUE_FIXTURE = {
	ok: true,
	queue_key: 'ready-to-plan',
	total: 1,
	rows: [
		{
			demand: {
				id: 'DEM-READY-001',
				code: 'DEM-MOH-2026-READY-001',
				name: 'District Hospital Renovation Works',
			},
			category: 'Works',
			estimated_value: 98000000,
			currency: 'KES',
			budget_line: { id: 'BL-001', code: 'BL-MOH-2026-001', name: 'Capital Works' },
			planning_status: 'Ready for Planning',
			blocker_summary: null,
		},
	],
	filters_applied: { queue: 'ready-to-plan' },
};

const READY_DRAWER_FIXTURE = {
	ok: true,
	demand: {
		id: 'DEM-READY-001',
		code: 'DEM-MOH-2026-READY-001',
		name: 'District Hospital Renovation Works',
		planning_status: 'Ready for Planning',
		category: 'Works',
		estimated_value: 98000000,
		currency: 'KES',
	},
	budget_context: {
		budget_line: { id: 'BL-001', code: 'BL-MOH-2026-001', name: 'Capital Works' },
	},
	target_plan: {
		id: 'PROC-PLAN-2026-2027',
		code: 'PLAN-MOH-2026',
		name: 'Ministry of Health Procurement Plan FY 2026/2027',
	},
	demand_items: [{ code: 'DEMI-MOH-2026-001' }],
	eligibility: { allowed: true, blockers: [] },
	actions: {
		include_in_plan: true,
		approval_certificate_route: '/app/demand/DEM-READY-001',
	},
};

async function expandRightPanel(page: import('@playwright/test').Page) {
	const shell = page.getByTestId('pp2-primary-workspace-shell');
	await expect(shell).toBeVisible({ timeout: 30000 });
	if ((await shell.getAttribute('data-right-panel-collapsed')) === '1') {
		await page.getByTestId('pp2-primary-right-panel-toggle').click();
		await expect(shell).toHaveAttribute('data-right-panel-collapsed', '0');
	}
}

async function setupApis(page: import('@playwright/test').Page, mode: 'ok' | 'error' = 'ok') {
	await page.route(APPROVED_DEMANDS_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: READY_QUEUE_FIXTURE }),
		});
	});
	await page.route(APPROVED_DEMAND_DRAWER_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: READY_DRAWER_FIXTURE }),
		});
	});
	await page.route(INCLUDE_DEMAND_API, async (route) => {
		if (mode === 'error') {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: false,
						message:
							'Cannot proceed with PLANINCL-MOH-2026-001 because source object and target object technical refs are inconsistent.',
					},
				}),
			});
			return;
		}
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				message: {
					ok: true,
					action: 'created',
					inclusion_code: 'PLANINCL-MOH-2026-001',
					demand_code: 'DEM-MOH-2026-READY-001',
					procurement_plan_code: 'PLAN-MOH-2026',
				},
			}),
		});
	});
	await page.route(PLAN_SEARCH_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				message: [
					{
						value: 'PLAN-MOH-2026',
						description: 'Ministry of Health Procurement Plan FY 2026/2027',
					},
				],
			}),
		});
	});
}

async function submitInclude(page: import('@playwright/test').Page) {
	await page.getByTestId('pp2-approved-demand-row').first().click();
	await expect(page.getByTestId('pp2-approved-demand-summary')).toBeVisible({ timeout: 30000 });
	await page.getByTestId('pp2-include-in-plan-button').click();
	await expect(page.getByTestId('pp2-include-plan-modal')).toBeVisible({ timeout: 30000 });
}

async function confirmIncludeFromOpenModal(page: import('@playwright/test').Page) {
	await page.getByTestId('pp2-target-plan-select-input').fill('PLAN-MOH-2026');
	await page.evaluate(() => {
		const dialog = (window as unknown as {
			cur_dialog?: {
				set_value?: (fieldname: string, value: string) => void;
				primary_action?: (values?: Record<string, string>) => void;
				fields_dict?: Record<string, { set_value?: (value: string) => void }>;
			};
		}).cur_dialog;
		if (!dialog) return;
		if (dialog.fields_dict?.target_plan?.set_value) {
			dialog.fields_dict.target_plan.set_value('PLAN-MOH-2026');
		}
		if (dialog.fields_dict?.target_plan_fallback?.set_value) {
			dialog.fields_dict.target_plan_fallback.set_value('PLAN-MOH-2026');
		}
		if (typeof dialog.set_value === 'function') {
			dialog.set_value('target_plan', 'PLAN-MOH-2026');
			dialog.set_value('target_plan_fallback', 'PLAN-MOH-2026');
		}
		if (typeof dialog.primary_action === 'function') {
			dialog.primary_action({
				target_plan: 'PLAN-MOH-2026',
				target_plan_fallback: 'PLAN-MOH-2026',
			});
		}
	});
}

function assertNoTechnicalLeakage(locator: import('@playwright/test').Locator) {
	return Promise.all(
		FORBIDDEN_TECHNICAL_COPY.map(async (pattern) => {
			await expect(locator).not.toContainText(pattern);
		})
	);
}

test.describe('P5C-015 Include technical hiding', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('ordinary modal and success copy do not leak technical IDs', async ({ page }) => {
		await setupApis(page, 'ok');
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await page.getByTestId('pp2-approved-demand-row').first().click();
		await page.getByTestId('pp2-include-in-plan-button').click();

		const modal = page.getByTestId('pp2-include-plan-modal');
		await expect(modal).toBeVisible({ timeout: 30000 });
		await assertNoTechnicalLeakage(modal);

		await confirmIncludeFromOpenModal(page);
		const success = page.getByTestId('pp2-include-plan-success');
		await expect(success).toBeVisible({ timeout: 30000 });
		await assertNoTechnicalLeakage(success);
		await assertNoTechnicalLeakage(page.locator('body'));
		await page.screenshot({ path: 'p5c015_include_technical_hiding.png', fullPage: true });
	});

	test('include error messaging does not leak backend technical IDs', async ({ page }) => {
		await setupApis(page, 'error');
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await submitInclude(page);
		await confirmIncludeFromOpenModal(page);

		const body = page.locator('body');
		await assertNoTechnicalLeakage(body);
		await expect(body).toContainText('The demand could not be included in the selected plan.');
	});
});
