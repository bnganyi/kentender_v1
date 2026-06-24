/**
 * P4-008 — Plan evidence action opens Evidence Drawer on request.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const EVIDENCE_FIXTURE = {
	ok: true,
	title: 'Ministry of Health Procurement Plan',
	timeline: [
		{ label: 'Procurement plan created', status: 'complete' },
		{ label: 'Procurement plan activated', status: 'complete' },
	],
	records: [{ label: 'Procurement Plan', type: 'procurement_plan' }],
	technical_details: { visible_by_default: false, requires_permission: true, may_view_technical: true },
};

async function mockPlansApis(page: import('@playwright/test').Page): Promise<void> {
	await page.route('**/api/method/**', async (route) => {
		const url = route.request().url();
		if (url.includes('get_pp_procurement_plan_evidence_view_model')) {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: EVIDENCE_FIXTURE }),
			});
			return;
		}
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
						show_view_evidence: true,
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

test.describe('P4-008 Plan evidence action', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await mockPlansApis(page);
	});

	test('View Evidence opens plan evidence drawer on request', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-evidence-drawer')).toHaveCount(0);
		await page.getByTestId('pp3-view-plan-evidence').click();
		const drawer = page.getByTestId('pp3-evidence-drawer');
		await expect(drawer).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp3-evidence-title')).toContainText('Ministry of Health Procurement Plan');
		await expect(page.getByTestId('pp3-evidence-timeline')).toContainText('Procurement plan created');
		await page.screenshot({ path: 'artifacts/p4-008-plan-evidence-drawer.png', fullPage: true });
	});
});
