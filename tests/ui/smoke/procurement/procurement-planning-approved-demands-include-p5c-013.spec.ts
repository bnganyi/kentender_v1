/**
 * P5C-013 — Approved Demands Include-in-Plan modal.
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

const BLOCKED_QUEUE_FIXTURE = {
	ok: true,
	queue_key: 'blocked',
	total: 1,
	rows: [
		{
			demand: {
				id: 'DEM-BLOCKED-001',
				code: 'DEM-MOH-2026-BLOCKED-001',
				name: 'County Health Center Demand',
			},
			category: 'Works',
			estimated_value: 9800000,
			currency: 'KES',
			budget_line: { id: '', code: '', name: '' },
			planning_status: 'Blocked',
			blocker_summary: { count: 1, label: 'Missing approved budget link' },
		},
	],
	filters_applied: { queue: 'blocked' },
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
	demand_items: [{ code: 'DEMI-MOH-2026-001' }, { code: 'DEMI-MOH-2026-002' }],
	eligibility: { allowed: true, blockers: [] },
	actions: {
		include_in_plan: true,
		approval_certificate_route: '/app/demand/DEM-READY-001',
	},
};

const BLOCKED_DRAWER_FIXTURE = {
	ok: true,
	demand: {
		id: 'DEM-BLOCKED-001',
		code: 'DEM-MOH-2026-BLOCKED-001',
		name: 'County Health Center Demand',
		planning_status: 'Blocked',
		category: 'Works',
		estimated_value: 9800000,
		currency: 'KES',
	},
	budget_context: {
		budget_line: { id: '', code: '', name: '' },
	},
	target_plan: null,
	demand_items: [{ code: 'DEMI-MOH-2026-101' }],
	eligibility: {
		allowed: false,
		blockers: [{ code: 'PP2-BLOCK-BUDGET', message: 'Missing approved budget link' }],
	},
	actions: {
		include_in_plan: false,
		approval_certificate_route: '/app/demand/DEM-BLOCKED-001',
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

async function mockIncludeModalApis(page: import('@playwright/test').Page) {
	await page.route(APPROVED_DEMANDS_QUEUE_API, async (route) => {
		const body = route.request().postData() || '';
		const queue = (new URLSearchParams(body).get('queue') || 'ready-to-plan').trim();
		const payload = queue === 'blocked' ? BLOCKED_QUEUE_FIXTURE : READY_QUEUE_FIXTURE;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
	await page.route(APPROVED_DEMAND_DRAWER_API, async (route) => {
		const body = route.request().postData() || '';
		const demandCode = (new URLSearchParams(body).get('demand_code') || '').trim();
		const payload =
			demandCode === 'DEM-MOH-2026-BLOCKED-001' ? BLOCKED_DRAWER_FIXTURE : READY_DRAWER_FIXTURE;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
	await page.route(INCLUDE_DEMAND_API, async (route) => {
		const body = route.request().postData() || '';
		const form = new URLSearchParams(body);
		const demandCode = (form.get('demand_code') || '').trim();
		const planCode = (form.get('procurement_plan_code') || '').trim();
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({
				message: {
					ok: true,
					action: 'created',
					inclusion_code: 'PLANINCL-MOH-2026-001',
					demand_code: demandCode,
					procurement_plan_code: planCode,
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

test.describe('P5C-013 Include in Plan modal', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await mockIncludeModalApis(page);
	});

	test('opens modal on eligible demand and submits include action', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await page.getByTestId('pp2-approved-demand-row').first().click();
		await expect(page.getByTestId('pp2-approved-demand-summary')).toBeVisible({ timeout: 30000 });
		await page.waitForTimeout(500);
		await page.getByTestId('pp2-include-in-plan-button').click();

		const modal = page.getByTestId('pp2-include-plan-modal');
		await expect(modal).toBeVisible({ timeout: 30000 });
		await expect(modal).toContainText('District Hospital Renovation Works');
		await expect(modal).toContainText('98,000,000 KES');
		await expect(modal).toContainText('Budget linked');
		await expect(page.getByTestId('pp2-target-plan-select')).toBeVisible();
		await page.getByTestId('pp2-target-plan-select-input').fill('PLAN-MOH-2026');
		await page.evaluate(() => {
			const dialog = (window as unknown as {
				cur_dialog?: {
					set_value?: (fieldname: string, value: string) => void;
					get_value?: (fieldname: string) => string;
					fields_dict?: Record<string, { set_value?: (value: string) => void }>;
				};
			}).cur_dialog;
			if (!dialog) return;
			if (dialog.fields_dict && dialog.fields_dict.target_plan && dialog.fields_dict.target_plan.set_value) {
				dialog.fields_dict.target_plan.set_value('PLAN-MOH-2026');
			}
			if (
				dialog.fields_dict &&
				dialog.fields_dict.target_plan_fallback &&
				dialog.fields_dict.target_plan_fallback.set_value
			) {
				dialog.fields_dict.target_plan_fallback.set_value('PLAN-MOH-2026');
			}
			if (typeof dialog.set_value === 'function') {
				dialog.set_value('target_plan', 'PLAN-MOH-2026');
				dialog.set_value('target_plan_fallback', 'PLAN-MOH-2026');
			}
		});
		await page.getByTestId('pp2-confirm-include-plan').click({ force: true });
	});

	test('blocked demand does not open modal and shows concise blocker reason', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await page.getByTestId('pp2-approved-demand-row').first().click();
		await page.getByTestId('pp2-include-in-plan-button').click();

		await expect(page.getByTestId('pp2-include-plan-modal')).toHaveCount(0);
		await expect(page.getByTestId('pp2-approved-demand-include-alert')).toContainText(
			'Missing approved budget link'
		);
	});
});
