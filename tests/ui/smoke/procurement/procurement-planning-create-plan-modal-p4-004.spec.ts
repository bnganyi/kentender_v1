/**
 * P4-004 — Create Plan modal provides entity, fiscal year, title, currency, create action.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PLANS_LIST_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plans_list';
const CREATE_PLAN_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.create_pp_procurement_plan';

const PLANS_LIST_FIXTURE = {
	ok: true,
	role_key: 'authority',
	plans: [],
};

async function mockPlansApis(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const request = route.request();
		const url = request.url();
		const postData = request.postData() || '';
		if (url.includes('create_pp_procurement_plan') || postData.includes(CREATE_PLAN_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						plan: {
							plan_id: 'PLAN-MOH-2027',
							title: 'Ministry of Health Procurement Plan FY 2027/2028',
							status_label: 'Draft',
						},
					},
				}),
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

test.describe('P4-004 Create Plan modal', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('plans page opens create plan modal with required fields', async ({ page }) => {
		await mockPlansApis(page);
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });

		await page.getByTestId('pp3-create-plan-button').click();
		const modal = page.getByTestId('pp3-create-plan-modal');
		await expect(modal).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-create-plan-entity')).toBeVisible();
		await expect(page.getByTestId('pp3-create-plan-fiscal-year')).toBeVisible();
		await expect(page.getByTestId('pp3-create-plan-title')).toBeVisible();
		await expect(page.getByTestId('pp3-create-plan-currency')).toBeVisible();
		await expect(page.getByTestId('pp3-create-plan-submit')).toBeVisible();

		await page.screenshot({ path: 'artifacts/p4-004-create-plan-modal.png', fullPage: true });
	});
});
