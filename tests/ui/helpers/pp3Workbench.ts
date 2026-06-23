import type { Page } from '@playwright/test';

export const pp3Root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

export const ACTIVE_PLAN_API =
	'**/api/method/**get_pp_active_plan_view_model*';

export const WORKLIST_API =
	'**/api/method/**get_pp_workbench_item_view_model*';

export const ACTIVE_FIXTURE = {
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

export async function mockActivePlan(page: Page): Promise<void> {
	await page.route(ACTIVE_PLAN_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: ACTIVE_FIXTURE }),
		});
	});
}

export async function mockWorkbenchItems(
	page: Page,
	payload: object,
): Promise<void> {
	await page.route(WORKLIST_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

export async function prepareWorkbenchSession(page: Page): Promise<void> {
	await page.evaluate(() => {
		window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
	});
}
