/**
 * P4-007 — Open in Workbench navigates to Workbench root.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

async function mockPlansApis(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const url = route.request().url();
		if (url.includes('get_pp_procurement_plan_summary')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({
					message: {
						ok: true,
						plan_id: 'PLAN-MOH-2026',
						title: 'Ministry of Health Procurement Plan',
						status_label: 'Active',
						fiscal_year: '2026/2027',
						demands_count: 1,
						packages_count: 1,
						released_count: 1,
						blockers_label: 'None',
						show_open_in_workbench: true,
					},
				}),
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

test.describe('P4-007 Open in Workbench', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await mockPlansApis(page);
	});

	test('Open in Workbench navigates to planning workbench root', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		await page.getByTestId('pp3-open-plan-in-workbench').click();
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/?(\?|$)/, { timeout: 30000 });
		await expect(page.getByTestId('pp3-planning-workbench')).toHaveCount(1);
		await page.screenshot({ path: 'artifacts/p4-007-open-plan-in-workbench.png', fullPage: true });
	});
});
