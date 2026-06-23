/**
 * P3-003 — Workbench active plan banner with enabled queue chrome.
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

const VIEW_ONLY_FIXTURE = {
	...ACTIVE_FIXTURE,
	can_change_plan: false,
	can_view_plan: true,
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

test.describe('P3-003 Active plan banner', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('shows active plan banner with Change/View actions and enabled queues', async ({ page }) => {
		await mockActivePlan(page, ACTIVE_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		const banner = page.getByTestId('pp3-active-plan-banner');
		await expect(banner).toBeVisible({ timeout: 30000 });
		await expect(banner).toContainText('Active plan: Ministry of Health Procurement Plan FY 2026/2027');
		await expect(banner).toContainText('PLAN-MOH-2026');
		await expect(banner).toContainText('2026/2027');
		await expect(page.getByTestId('pp3-change-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-view-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-no-active-plan-gate')).toHaveCount(0);
		await expect(page.getByTestId('pp3-create-plan-button')).toHaveCount(0);
		await expect(page.getByTestId('pp3-activate-plan-button')).toHaveCount(0);
		await expect(page.getByTestId('pp3-planning-work-unavailable')).toHaveCount(0);
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible();
		await expect(page.getByTestId('pp3-queue-needs-planning')).toBeVisible();

		await page.screenshot({ path: 'artifacts/p3-003-active-plan-banner.png', fullPage: true });
	});

	test('hides Change Plan when user may view but not change active plan', async ({ page }) => {
		await mockActivePlan(page, VIEW_ONLY_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp3-active-plan-banner')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-change-plan-button')).toHaveCount(0);
		await expect(page.getByTestId('pp3-view-plan-button')).toBeVisible();
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible();
	});
});
