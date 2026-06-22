/**
 * P5C-010 — Approved Demands queue behavior (Ready to Plan / Blocked / Already Planned).
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const APPROVED_DEMANDS_API =
	'**/api/method/**get_pp_approved_demands_awaiting_planning*';

const READY_FIXTURE = {
	ok: true,
	queue_key: 'ready-to-plan',
	total: 1,
	rows: [
		{
			demand: {
				id: 'DEM-READY-001',
				code: 'DEM-MOH-2026-READY-001',
				name: 'District Hospital Renovation Works',
			},
			category: 'Works',
			estimated_value: 98000000,
			currency: 'KES',
			planning_status: 'Ready for Planning',
			blocker_summary: null,
		},
	],
	filters_applied: { queue: 'ready-to-plan' },
};

const BLOCKED_FIXTURE = {
	ok: true,
	queue_key: 'blocked',
	total: 1,
	rows: [
		{
			demand: {
				id: 'DEM-BLOCKED-001',
				code: 'DEM-MOH-2026-BLOCKED-001',
				name: 'County Health Center Demand',
			},
			category: 'Works',
			estimated_value: 9800000,
			currency: 'KES',
			planning_status: 'Blocked',
			blocker_summary: { count: 1, label: 'Missing approved budget link' },
		},
	],
	filters_applied: { queue: 'blocked' },
};

const ALREADY_PLANNED_FIXTURE = {
	ok: true,
	queue_key: 'already-planned',
	total: 1,
	rows: [
		{
			demand: {
				id: 'DEM-PLANNED-001',
				code: 'DEM-MOH-2026-PLANNED-001',
				name: 'Regional Lab Equipment Demand',
			},
			category: 'Goods',
			estimated_value: 12500000,
			currency: 'KES',
			planning_status: 'Fully Planned',
			blocker_summary: null,
		},
	],
	filters_applied: { queue: 'already-planned' },
};

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/feature content (is )?intentionally deferred/i,
	/\bstub content\b/i,
	/workflow trace/i,
	/source object/i,
	/target object/i,
	/technical refs/i,
];

async function mockApprovedDemandsQueues(page: import('@playwright/test').Page) {
	await page.route(APPROVED_DEMANDS_API, async (route) => {
		const url = new URL(route.request().url());
		let queue = (url.searchParams.get('queue') || '').trim();
		if (!queue) {
			const body = route.request().postData() || '';
			const form = new URLSearchParams(body);
			queue = (form.get('queue') || '').trim();
		}
		if (!queue) queue = 'ready-to-plan';
		const payload =
			queue === 'blocked'
				? BLOCKED_FIXTURE
				: queue === 'already-planned'
					? ALREADY_PLANNED_FIXTURE
					: READY_FIXTURE;
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

test.describe('P5C-010 Approved Demands queues', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows three queue chips in required order with Ready to Plan active by default', async ({
		page,
	}) => {
		await mockApprovedDemandsQueues(page);
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		const tabs = page.getByTestId('pp2-queue-tabs');
		await expect(tabs).toBeVisible({ timeout: 30000 });
		const chips = tabs.locator('[role="tab"]');
		await expect(chips).toHaveCount(3);
		await expect(chips.nth(0)).toContainText('Ready to Plan');
		await expect(chips.nth(1)).toContainText('Blocked');
		await expect(chips.nth(2)).toContainText('Already Planned');
		await expect(page.getByTestId('pp2-queue-tab-ready-to-plan')).toHaveAttribute(
			'aria-selected',
			'true'
		);
		await expect(page.getByText('District Hospital Renovation Works')).toBeVisible();
	});

	test('loads blocked and already-planned queue from deep-link query', async ({ page }) => {
		await mockApprovedDemandsQueues(page);

		await page.goto(`${root}/desk/procurement-planning/approved-demands?queue=blocked`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-queue-tab-blocked')).toHaveAttribute('aria-selected', 'true');
		await expect(page.getByText('County Health Center Demand')).toBeVisible();

		await page.goto(`${root}/desk/procurement-planning/approved-demands?queue=already-planned`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-queue-tab-already-planned')).toHaveAttribute(
			'aria-selected',
			'true'
		);
		await expect(page.getByText('Regional Lab Equipment Demand')).toBeVisible();
	});

	test('switches queue chip, updates query, and renders queue-specific row', async ({ page }) => {
		await mockApprovedDemandsQueues(page);
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByText('District Hospital Renovation Works')).toBeVisible();

		await page.getByTestId('pp2-queue-tab-blocked').click();
		await expect(page).toHaveURL(/queue=blocked/);
		await expect(page.getByTestId('pp2-queue-tab-blocked')).toHaveAttribute('aria-selected', 'true');
		await expect(page.getByText('County Health Center Demand')).toBeVisible();

		await page.getByTestId('pp2-queue-tab-already-planned').click();
		await expect(page).toHaveURL(/queue=already-planned/);
		await expect(page.getByTestId('pp2-queue-tab-already-planned')).toHaveAttribute(
			'aria-selected',
			'true'
		);
		await expect(page.getByText('Regional Lab Equipment Demand')).toBeVisible();
	});

	test('contains no forbidden implementation or handoff technical copy', async ({ page }) => {
		await mockApprovedDemandsQueues(page);
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-approved-demands-page')).toBeVisible({ timeout: 30000 });
		const bodyText = await page.locator('body').innerText();
		for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});
