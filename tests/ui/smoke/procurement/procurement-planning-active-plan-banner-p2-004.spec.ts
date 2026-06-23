/**
 * P2-004 — ActivePlanBanner renders no-active and active plan states.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const ACTIVE_PLAN_API =
	'**/api/method/**get_pp_active_plan_view_model*';

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

const NO_ACTIVE_FIXTURE = {
	ok: true,
	role_key: 'planner',
	has_active_plan: false,
	fiscal_year: '2026/2027',
	message: 'No active procurement plan exists for FY 2026/2027.',
	primary_action: { label: 'Create Plan', action: 'create_plan' },
	secondary_action: { label: 'Activate Existing Plan', action: 'activate_existing_plan' },
	can_change_plan: false,
	can_view_plan: false,
};

async function mockActivePlan(
	page: import('@playwright/test').Page,
	payload: object,
) {
	await page.route(ACTIVE_PLAN_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

test.describe('P2-004 ActivePlanBanner', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders no-active-plan gate with Create/Activate actions', async ({ page }) => {
		await mockActivePlan(page, NO_ACTIVE_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-no-active-plan-gate')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-create-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-activate-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-no-active-plan-gate')).toContainText(
			'No active procurement plan exists for FY 2026/2027.'
		);
		await expect(page.getByTestId('pp3-active-plan-banner')).toHaveCount(0);
		await expect(page.getByTestId('pp3-change-plan-button')).toHaveCount(0);
		await expect(page.getByTestId('pp3-view-plan-button')).toHaveCount(0);
		await page.screenshot({ path: 'artifacts/p2-004-no-active-plan-gate.png', fullPage: true });
	});

	test('renders active plan banner with Change/View actions', async ({ page }) => {
		await mockActivePlan(page, ACTIVE_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-active-plan-banner')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-active-plan-banner')).toContainText(
			'Active plan: Ministry of Health Procurement Plan FY 2026/2027'
		);
		await expect(page.getByTestId('pp3-change-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-view-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-no-active-plan-gate')).toHaveCount(0);
		await expect(page.getByTestId('pp3-create-plan-button')).toHaveCount(0);
		await expect(page.getByTestId('pp3-activate-plan-button')).toHaveCount(0);
		await page.screenshot({ path: 'artifacts/p2-004-active-plan-banner.png', fullPage: true });
	});
});
