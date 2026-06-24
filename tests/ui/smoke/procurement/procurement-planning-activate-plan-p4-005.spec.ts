/**
 * P4-005 — Activate Plan flow for permitted user.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const SUMMARY_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plan_summary';
const ACTIVATE_METHOD =
	'kentender_procurement.procurement_planning.api.procurement_plans.activate_pp_procurement_plan';

const DRAFT_SUMMARY = {
	ok: true,
	plan_id: 'PLAN-MOH-DRAFT',
	title: 'Draft Plan',
	status_label: 'Draft',
	fiscal_year: '2026/2027',
	demands_count: 0,
	packages_count: 0,
	released_count: 0,
	blockers_label: 'None',
	show_activate_plan: true,
	show_close_plan: false,
	show_open_in_workbench: true,
	show_view_evidence: true,
};

async function mockApis(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const url = route.request().url();
		const postData = route.request().postData() || '';
		if (url.includes('activate_pp_procurement_plan') || postData.includes(ACTIVATE_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: { ...DRAFT_SUMMARY, status_label: 'Active', show_activate_plan: false, show_close_plan: true },
				}),
			});
			return;
		}
		if (url.includes('get_pp_procurement_plan_summary') || postData.includes(SUMMARY_METHOD)) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: DRAFT_SUMMARY }),
			});
			return;
		}
		if (url.includes('get_pp_procurement_plans_list')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						plans: [{ plan_id: 'PLAN-MOH-DRAFT', title: 'Draft Plan', fiscal_year: '2026/2027', status_label: 'Draft', counts_label: '0 demands · 0 packages · 0 released' }],
					},
				}),
			});
			return;
		}
		await route.continue();
	});
}

test.describe('P4-005 Activate Plan flow', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await mockApis(page);
	});

	test('draft plan summary shows Activate Plan for permitted user', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		const activate = page.getByTestId('pp3-activate-plan-button');
		await expect(activate).toBeVisible({ timeout: 30000 });
		await activate.click();
		await expect(page.getByTestId('pp3-plan-summary-status')).toHaveText('Active', { timeout: 30000 });
		await page.screenshot({ path: 'artifacts/p4-005-activate-plan-flow.png', fullPage: true });
	});
});
