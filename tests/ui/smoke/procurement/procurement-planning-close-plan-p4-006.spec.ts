/**
 * P4-006 — Close Plan flow for permitted user.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const ACTIVE_SUMMARY = {
	ok: true,
	plan_id: 'PLAN-MOH-2026',
	title: 'Ministry of Health Procurement Plan',
	status_label: 'Active',
	fiscal_year: '2026/2027',
	demands_count: 1,
	packages_count: 1,
	released_count: 1,
	blockers_label: 'None',
	show_activate_plan: false,
	show_close_plan: true,
	show_open_in_workbench: true,
	show_view_evidence: true,
};

async function mockApis(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const url = route.request().url();
		if (url.includes('close_pp_procurement_plan')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: { ...ACTIVE_SUMMARY, status_label: 'Closed', show_close_plan: false },
				}),
			});
			return;
		}
		if (url.includes('get_pp_procurement_plan_summary')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: ACTIVE_SUMMARY }),
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
						plans: [{ plan_id: 'PLAN-MOH-2026', title: 'Ministry of Health Procurement Plan', fiscal_year: '2026/2027', status_label: 'Active', counts_label: '1 demand · 1 package · 1 released' }],
					},
				}),
			});
			return;
		}
		await route.continue();
	});
}

test.describe('P4-006 Close Plan flow', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await mockApis(page);
	});

	test('active plan summary shows Close Plan for permitted user', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		const closeBtn = page.getByTestId('pp3-close-plan-button');
		await expect(closeBtn).toBeVisible({ timeout: 30000 });
		await closeBtn.click();
		await expect(page.getByTestId('pp3-plan-summary-status')).toHaveText('Closed', { timeout: 30000 });
		await page.screenshot({ path: 'artifacts/p4-006-close-plan-flow.png', fullPage: true });
	});
});
