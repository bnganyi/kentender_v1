/**
 * P5C-008 — Planning Home must not show handoff/evidence stacks.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const NEEDS_PLANNING_QUEUE_API =
	'**/api/method/**get_pp_planning_home_needs_planning_queue*';
const NEEDS_REVIEW_QUEUE_API =
	'**/api/method/**get_pp_planning_home_needs_review_queue*';
const READY_RELEASE_QUEUE_API =
	'**/api/method/**get_pp_planning_home_ready_to_release_queue*';
const RELEASED_RECENTLY_QUEUE_API =
	'**/api/method/**get_pp_planning_home_released_recently_queue*';
const BLOCKED_QUEUE_API =
	'**/api/method/**get_pp_planning_home_blocked_queue*';

const NEEDS_PLANNING_FIXTURE = {
	ok: true,
	queue_key: 'needs_planning',
	total: 1,
	limit: 5,
	view_all_href: '/desk/procurement-planning/approved-demands',
	items: [
		{
			id: 'DEM-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Works · 98,000,000 KES · Budget linked',
			next_action_label: 'Include in procurement plan',
			primary_action: { label: 'Open', action: 'open_demand', target: 'DEM-001' },
		},
	],
};

const NEEDS_REVIEW_FIXTURE = {
	ok: true,
	queue_key: 'needs_review',
	total: 1,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=needs-review',
	items: [
		{
			id: 'PKG-001',
			title: 'Regional Clinic Equipment Package',
			subtitle: 'Goods · Open Tender · 12,500,000 KES',
			next_action_label: 'Review package',
			primary_action: { label: 'Open', action: 'open_package', target: 'PKG-001' },
		},
	],
};

const READY_RELEASE_FIXTURE = {
	ok: true,
	queue_key: 'ready_to_release',
	total: 1,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=ready-to-release',
	items: [
		{
			id: 'PKG-002',
			title: 'Referral Hospital HVAC Package',
			subtitle: 'Works · Open Tender · 44,000,000 KES',
			next_action_label: 'Release package',
			primary_action: { label: 'Open', action: 'open_package', target: 'PKG-002' },
		},
	],
};

const RELEASED_RECENTLY_FIXTURE = {
	ok: true,
	queue_key: 'released_recently',
	total: 1,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=released-recently',
	items: [
		{
			id: 'PKG-003',
			title: 'Laboratory Equipment Package',
			subtitle: 'Released to Tender Management · Tender created',
			next_action_label: 'Continue in Tender Management',
			primary_action: {
				label: 'Open Tender',
				action: 'open_tender',
				target: 'TND-MOH-2026-003',
			},
			secondary_actions: [
				{
					label: 'View Package',
					action: 'open_package',
					target: 'PKG-003',
				},
			],
		},
	],
};

const BLOCKED_FIXTURE = {
	ok: true,
	queue_key: 'blocked',
	total: 1,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=blocked',
	items: [
		{
			id: 'DEM-004',
			title: 'County Health Center Demand',
			subtitle: 'Works · 9,800,000 KES · Missing approved budget link',
			next_action_label: 'Resolve blocker',
			primary_action: {
				label: 'Resolve blocker',
				action: 'open_demand',
				target: 'DEM-004',
			},
		},
	],
};

const FORBIDDEN_TESTIDS = [
	'pp2-package-handoff-stack',
	'pp2-planning-handoff-card',
	'pp2-planning-handoff-business-mode',
	'pp2-handoff-card-technical-details',
	'pp2-planning-handoff-technical-toggle',
	'pp2-technical-details-toggle',
	'pp2-technical-details-panel',
	'pp2-evidence-drawer',
	'pp2-evidence-timeline',
	'pp2-evidence-record-list',
	'pp2-selected-summary-panel',
	'pp2-queue-tabs',
	'pp2-work-list',
	'pp2-surface-empty-state',
];

const FORBIDDEN_COPY = [
	/workflow trace/i,
	/source object/i,
	/target object/i,
	/technical refs/i,
	/shell baseline active/i,
	/feature content deferred/i,
	/stub content/i,
];

async function mockHomeQueues(page: import('@playwright/test').Page) {
	await page.route(NEEDS_PLANNING_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NEEDS_PLANNING_FIXTURE }),
		});
	});
	await page.route(NEEDS_REVIEW_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NEEDS_REVIEW_FIXTURE }),
		});
	});
	await page.route(READY_RELEASE_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: READY_RELEASE_FIXTURE }),
		});
	});
	await page.route(RELEASED_RECENTLY_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: RELEASED_RECENTLY_FIXTURE }),
		});
	});
	await page.route(BLOCKED_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: BLOCKED_FIXTURE }),
		});
	});
}

test.describe('P5C-008 Planning Home no handoff stacks', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('keeps Planning Home queue-first with no handoff/evidence/technical stack surfaces', async ({
		page,
	}) => {
		await mockHomeQueues(page);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-summary')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-needs-review')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-released-recently')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-blocked')).toBeVisible({ timeout: 30000 });

		for (const testId of FORBIDDEN_TESTIDS) {
			await expect(page.getByTestId(testId)).toHaveCount(0);
		}

		const homeText = (await page.getByTestId('pp2-planning-home-surface').innerText()) || '';
		for (const pattern of FORBIDDEN_COPY) {
			expect(homeText).not.toMatch(pattern);
		}

		await expect(page.getByText('Planning Inclusion Record')).toHaveCount(0);
		await expect(page.getByText('Planning Release Package')).toHaveCount(0);
		await expect(page.getByText('Tender Consumption Record')).toHaveCount(0);
	});
});
