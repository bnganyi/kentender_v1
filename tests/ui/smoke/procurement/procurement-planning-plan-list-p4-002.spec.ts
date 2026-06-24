/**
 * P4-002 — Procurement Plans list shows title, fiscal year, status, counts.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PLANS_LIST_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plans_list';

const PLANS_LIST_FIXTURE = {
	ok: true,
	role_key: 'authority',
	plans: [
		{
			plan_id: 'PLAN-MOH-2026',
			plan_code: 'PLAN-MOH-2026',
			title: 'Ministry of Health Procurement Plan',
			fiscal_year: '2026/2027',
			status_label: 'Active',
			demands_count: 1,
			packages_count: 1,
			released_count: 1,
			counts_label: '1 demand · 1 package · 1 released',
			is_active_plan: true,
		},
	],
};

async function mockPlansList(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const request = route.request();
		const url = request.url();
		const postData = request.postData() || '';
		if (url.includes('get_pp_procurement_plans_list') || postData.includes(PLANS_LIST_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: PLANS_LIST_FIXTURE }),
			});
			return;
		}
		await route.continue();
	});
}

test.describe('P4-002 Procurement Plans list', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('plans route renders plan list rows with title, fiscal year, status, counts', async ({
		page,
	}) => {
		await mockPlansList(page);
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp3-plan-list')).toHaveCount(1);
		const row = page.getByTestId('pp3-plan-row').first();
		await expect(row).toBeVisible({ timeout: 30000 });
		await expect(row).toContainText('Ministry of Health Procurement Plan');
		await expect(row).toContainText('2026/2027');
		await expect(row).toContainText('Active');
		await expect(row).toContainText('1 demand · 1 package · 1 released');

		await page.screenshot({ path: 'artifacts/p4-002-procurement-plans-list.png', fullPage: true });
	});
});
