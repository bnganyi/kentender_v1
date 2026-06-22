/**
 * P5C-012 — Approved Demands selected summary contract.
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
	role_key: 'planning_authority',
	demand: {
		id: 'DEM-READY-001',
		code: 'DEM-MOH-2026-READY-001',
		name: 'District Hospital Renovation Works',
		status: 'Approved',
		planning_status: 'Ready for Planning',
		category: 'Works',
		estimated_value: 98000000,
		currency: 'KES',
	},
	budget_context: {
		budget_line: { id: 'BL-001', code: 'BL-MOH-2026-001', name: 'Capital Works' },
	},
	eligibility: { allowed: true, blockers: [] },
	evidence: { view_route: '/app/demand/DEM-READY-001' },
	actions: {
		include_in_plan: true,
		view_demand_approval_certificate: true,
		approval_certificate_route: '/app/demand/DEM-READY-001',
	},
};

const BLOCKED_DRAWER_FIXTURE = {
	ok: true,
	role_key: 'planning_authority',
	demand: {
		id: 'DEM-BLOCKED-001',
		code: 'DEM-MOH-2026-BLOCKED-001',
		name: 'County Health Center Demand',
		status: 'Approved',
		planning_status: 'Blocked',
		category: 'Works',
		estimated_value: 9800000,
		currency: 'KES',
	},
	budget_context: {
		budget_line: { id: '', code: '', name: '' },
	},
	eligibility: {
		allowed: false,
		blockers: [{ code: 'PP2-BLOCK-BUDGET', message: 'Missing approved budget link' }],
	},
	evidence: { view_route: '/app/demand/DEM-BLOCKED-001' },
	actions: {
		include_in_plan: false,
		view_demand_approval_certificate: true,
		approval_certificate_route: '/app/demand/DEM-BLOCKED-001',
	},
};

const FORBIDDEN_SUMMARY_COPY = [/PLANINCL-/i, /source object/i, /target object/i, /technical refs/i];

async function expandRightPanel(page: import('@playwright/test').Page) {
	const shell = page.getByTestId('pp2-primary-workspace-shell');
	await expect(shell).toBeVisible({ timeout: 30000 });
	if ((await shell.getAttribute('data-right-panel-collapsed')) === '1') {
		await page.getByTestId('pp2-primary-right-panel-toggle').click();
		await expect(shell).toHaveAttribute('data-right-panel-collapsed', '0');
	}
}

async function mockApprovedDemandApis(page: import('@playwright/test').Page) {
	await page.route(APPROVED_DEMANDS_QUEUE_API, async (route) => {
		const body = route.request().postData() || '';
		const form = new URLSearchParams(body);
		const queue = (form.get('queue') || 'ready-to-plan').trim();
		const payload = queue === 'blocked' ? BLOCKED_QUEUE_FIXTURE : READY_QUEUE_FIXTURE;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
	await page.route(APPROVED_DEMAND_DRAWER_API, async (route) => {
		const body = route.request().postData() || '';
		const form = new URLSearchParams(body);
		const demandCode = (form.get('demand_code') || '').trim();
		const payload =
			demandCode === 'DEM-MOH-2026-BLOCKED-001' ? BLOCKED_DRAWER_FIXTURE : READY_DRAWER_FIXTURE;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

test.describe('P5C-012 Approved Demands selected summary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
		await mockApprovedDemandApis(page);
	});

	test('renders selected demand summary fields and P5C-012 action selectors', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await page.getByTestId('pp2-approved-demand-row').first().click();

		const summary = page.getByTestId('pp2-approved-demand-summary');
		await expect(summary).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-selected-summary-title')).toHaveText(
			'District Hospital Renovation Works'
		);
		await expect(page.getByTestId('pp2-selected-summary-status')).toContainText('Ready for Planning');
		await expect(page.getByTestId('pp2-selected-summary-facts')).toContainText('Works');
		await expect(page.getByTestId('pp2-selected-summary-facts')).toContainText('98,000,000 KES');
		await expect(page.getByTestId('pp2-selected-summary-funding')).toContainText('Budget linked');
		await expect(page.getByTestId('pp2-selected-summary-blockers')).toContainText(/No blockers/i);
		await expect(page.getByTestId('pp2-selected-summary-next-action')).toContainText('Include in plan');
		await expect(page.getByTestId('pp2-include-in-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp2-view-demand-button')).toBeVisible();
		await expect(page.getByTestId('pp2-view-demand-evidence')).toBeVisible();
		await expect(summary).not.toContainText('DEM-MOH-2026-READY-001');
	});

	test('blocked queue shows blocker and include action remains click-safe placeholder', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await page.getByTestId('pp2-approved-demand-row').first().click();
		await expect(page.getByTestId('pp2-selected-summary-title')).toHaveText('County Health Center Demand');
		await expect(page.getByTestId('pp2-selected-summary-status')).toContainText('Blocked');
		await expect(page.getByTestId('pp2-selected-summary-funding')).toContainText('Budget not linked');
		await expect(page.getByTestId('pp2-selected-summary-blockers')).toContainText('Missing approved budget link');

		await page.getByTestId('pp2-include-in-plan-button').click();
		await expect(page.getByTestId('pp2-include-plan-modal')).toHaveCount(0);
		await expect(page).toHaveURL(/approved-demands\?queue=blocked/);
		await expect(page.getByTestId('pp2-approved-demand-summary')).toBeVisible();
	});

	test('contains no forbidden technical leakage in selected summary', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expandRightPanel(page);
		await page.getByTestId('pp2-approved-demand-row').first().click();
		const summaryText = await page.getByTestId('pp2-approved-demand-summary').innerText();
		for (const pattern of FORBIDDEN_SUMMARY_COPY) {
			expect(summaryText).not.toMatch(pattern);
		}
	});
});
