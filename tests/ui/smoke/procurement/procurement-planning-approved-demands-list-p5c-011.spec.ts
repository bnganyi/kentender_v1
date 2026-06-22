/**
 * P5C-011 — Approved Demands list row contract.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const APPROVED_DEMANDS_API =
	'**/api/method/**get_pp_approved_demands_awaiting_planning*';

const READY_FIXTURE = {
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

const BLOCKED_FIXTURE = {
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

const FORBIDDEN_COPY = [/workflow trace/i, /source object/i, /target object/i, /technical refs/i];

async function mockApprovedDemandRows(page: import('@playwright/test').Page) {
	await page.route(APPROVED_DEMANDS_API, async (route) => {
		const body = route.request().postData() || '';
		const form = new URLSearchParams(body);
		const queue = (form.get('queue') || 'ready-to-plan').trim();
		const payload = queue === 'blocked' ? BLOCKED_FIXTURE : READY_FIXTURE;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

test.describe('P5C-011 Approved Demands list rows', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders row contract fields for ready-to-plan demand', async ({ page }) => {
		await mockApprovedDemandRows(page);
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		const row = page.getByTestId('pp2-approved-demand-row').first();
		await expect(row).toBeVisible({ timeout: 30000 });
		await expect(row.getByTestId('pp2-approved-demand-row-title')).toHaveText(
			'District Hospital Renovation Works'
		);
		await expect(row.getByTestId('pp2-approved-demand-row-category-value')).toContainText('Works');
		await expect(row.getByTestId('pp2-approved-demand-row-category-value')).toContainText(
			'98,000,000 KES'
		);
		await expect(row.getByTestId('pp2-approved-demand-row-funding-status')).toHaveText('Budget linked');
		await expect(row.getByTestId('pp2-approved-demand-row-planning-status')).toHaveText(
			'Ready for Planning'
		);
		await expect(row.getByTestId('pp2-approved-demand-row-blocker')).toHaveCount(0);
		await expect(row).not.toContainText('DEM-MOH-2026-READY-001');
	});

	test('shows blocker marker and blocked planning status on blocked queue', async ({ page }) => {
		await mockApprovedDemandRows(page);
		await page.goto(`${root}/desk/procurement-planning/approved-demands?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});
		const row = page.getByTestId('pp2-approved-demand-row').first();
		await expect(row).toBeVisible({ timeout: 30000 });
		await expect(row.getByTestId('pp2-approved-demand-row-title')).toHaveText('County Health Center Demand');
		await expect(row.getByTestId('pp2-approved-demand-row-planning-status')).toHaveText('Blocked');
		await expect(row.getByTestId('pp2-approved-demand-row-blocker')).toContainText(
			'Missing approved budget link'
		);
		await expect(row.getByTestId('pp2-approved-demand-row-funding-status')).toHaveText(
			'Budget not linked'
		);
	});

	test('contains no forbidden technical leakage copy', async ({ page }) => {
		await mockApprovedDemandRows(page);
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-approved-demands-page')).toBeVisible({ timeout: 30000 });
		const bodyText = await page.locator('body').innerText();
		for (const pattern of FORBIDDEN_COPY) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});
