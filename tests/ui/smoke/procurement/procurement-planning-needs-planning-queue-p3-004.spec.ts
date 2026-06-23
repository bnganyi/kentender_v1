/**
 * P3-004 — Workbench Needs Planning queue shows approved demands ready to plan.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const ACTIVE_PLAN_API =
	'**/api/method/**get_pp_active_plan_view_model*';

const WORKLIST_API =
	'**/api/method/**get_pp_workbench_item_view_model*';

const ACTIVE_FIXTURE = {
	ok: true,
	role_key: 'planner',
	has_active_plan: true,
	plan_code: 'PLAN-MOH-2026',
	plan_title: 'Ministry of Health Procurement Plan FY 2026/2027',
	fiscal_year: '2026/2027',
	procuring_entity: 'Ministry of Health',
	status_label: 'Active',
	can_change_plan: true,
	can_view_plan: true,
};

const NEEDS_PLANNING_FIXTURE = {
	ok: true,
	queue: 'needs_planning',
	total: 1,
	start: 0,
	limit: 20,
	items: [
		{
			work_item_id: 'needs_planning:DEM-MOH-2026-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Works · 98,000,000 KES · Budget linked',
			state_label: 'Needs planning',
			next_action_label: 'Include in Plan',
			underlying_object_type: 'approved_demand',
		},
	],
};

const EMPTY_NEEDS_PLANNING_FIXTURE = {
	ok: true,
	queue: 'needs_planning',
	total: 0,
	start: 0,
	limit: 20,
	items: [],
};

const FORBIDDEN_LEAKAGE = [
	/DEM-MOH-2026-001/i,
	/PLANINCL-/i,
	/source_object_code/i,
	/target_object_code/i,
	/technical_refs_json/i,
];

async function mockActivePlan(
	page: import('@playwright/test').Page,
) {
	await page.route(ACTIVE_PLAN_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: ACTIVE_FIXTURE }),
		});
	});
}

async function mockWorkbenchItems(
	page: import('@playwright/test').Page,
	payload: object,
) {
	await page.route(WORKLIST_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

test.describe('P3-004 Needs Planning queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('shows approved demands with Include in Plan on default Needs Planning queue', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, NEEDS_PLANNING_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		const needsTab = page.getByTestId('pp3-queue-needs-planning');
		await expect(needsTab).toBeVisible({ timeout: 30000 });
		await expect(needsTab).toHaveClass(/is-active/);
		await expect(needsTab).toHaveAttribute('aria-selected', 'true');

		const workList = page.getByTestId('pp3-work-list');
		await expect(workList).toBeVisible();
		const row = page.getByTestId('pp3-work-item-row').first();
		await expect(row).toBeVisible();
		await expect(row.getByTestId('pp3-work-item-title')).toHaveText('District Hospital Renovation Works');
		await expect(row.getByTestId('pp3-work-item-state')).toHaveText('Needs planning');
		await expect(row.getByTestId('pp3-work-item-next-action')).toHaveText('Include in Plan');
		await expect(row).toContainText('Works');
		await expect(row).toContainText('Budget linked');

		const rowText = await row.innerText();
		for (const pattern of FORBIDDEN_LEAKAGE) {
			expect(rowText).not.toMatch(pattern);
		}

		await page.screenshot({ path: 'artifacts/p3-004-needs-planning-queue.png', fullPage: true });
	});

	test('shows Needs Planning empty state when no approved demands need planning', async ({ page }) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_NEEDS_PLANNING_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp3-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-work-list')).toBeVisible();
		await expect(page.getByTestId('pp3-work-list')).toContainText('No approved demands need planning.');
		await expect(page.getByTestId('pp3-work-item-row')).toHaveCount(0);
	});
});
