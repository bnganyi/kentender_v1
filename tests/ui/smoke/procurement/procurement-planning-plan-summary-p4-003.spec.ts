/**
 * P4-003 — Selected plan summary shows active state, demands, packages, released, blockers.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PLANS_LIST_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plans_list';
const PLAN_SUMMARY_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plan_summary';

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

const PLAN_SUMMARY_FIXTURE = {
	ok: true,
	role_key: 'authority',
	plan_id: 'PLAN-MOH-2026',
	title: 'Ministry of Health Procurement Plan',
	status_label: 'Active',
	fiscal_year: '2026/2027',
	demands_count: 1,
	packages_count: 1,
	released_count: 1,
	blockers_count: 0,
	blockers_label: 'None',
	is_active_plan: true,
};

async function mockPlansApis(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const request = route.request();
		const url = request.url();
		const postData = request.postData() || '';
		if (url.includes('get_pp_procurement_plan_summary') || postData.includes(PLAN_SUMMARY_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: PLAN_SUMMARY_FIXTURE }),
			});
			return;
		}
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

test.describe('P4-003 Selected plan summary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('plans route shows selected plan summary facts and blockers', async ({ page }) => {
		await mockPlansApis(page);
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });

		const summary = page.getByTestId('pp3-plan-summary');
		await expect(summary).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-plan-summary-status')).toHaveText('Active');
		await expect(page.getByTestId('pp3-plan-summary-fiscal-year')).toHaveText('2026/2027');
		await expect(page.getByTestId('pp3-plan-summary-demands')).toHaveText('1');
		await expect(page.getByTestId('pp3-plan-summary-packages')).toHaveText('1');
		await expect(page.getByTestId('pp3-plan-summary-released')).toHaveText('1');
		await expect(page.getByTestId('pp3-plan-summary-blockers')).toHaveText('None');

		await page.screenshot({ path: 'artifacts/p4-003-procurement-plan-summary.png', fullPage: true });
	});
});
