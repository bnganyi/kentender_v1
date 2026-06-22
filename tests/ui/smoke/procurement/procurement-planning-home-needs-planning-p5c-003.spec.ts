/**
 * P5C-003 — Planning Home Needs Planning queue section.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const QUEUE_API =
	'**/api/method/**get_pp_planning_home_needs_planning_queue*';

const NEEDS_REVIEW_QUEUE_API =
	'**/api/method/**get_pp_planning_home_needs_review_queue*';
const READY_RELEASE_QUEUE_API =
	'**/api/method/**get_pp_planning_home_ready_to_release_queue*';
const RELEASED_RECENTLY_QUEUE_API =
	'**/api/method/**get_pp_planning_home_released_recently_queue*';
const BLOCKED_QUEUE_API =
	'**/api/method/**get_pp_planning_home_blocked_queue*';

const NEEDS_REVIEW_EMPTY = {
	ok: true,
	queue_key: 'needs_review',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=needs-review',
	items: [],
};

const READY_RELEASE_EMPTY = {
	ok: true,
	queue_key: 'ready_to_release',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=ready-to-release',
	items: [],
};

const RELEASED_RECENTLY_EMPTY = {
	ok: true,
	queue_key: 'released_recently',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=released-recently',
	items: [],
};

const BLOCKED_EMPTY = {
	ok: true,
	queue_key: 'blocked',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=blocked',
	items: [],
};

async function mockNeedsReviewEmpty(page: import('@playwright/test').Page) {
	await page.route(NEEDS_REVIEW_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NEEDS_REVIEW_EMPTY }),
		});
	});
}

async function mockReadyReleaseEmpty(page: import('@playwright/test').Page) {
	await page.route(READY_RELEASE_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: READY_RELEASE_EMPTY }),
		});
	});
}

async function mockReleasedRecentlyEmpty(page: import('@playwright/test').Page) {
	await page.route(RELEASED_RECENTLY_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: RELEASED_RECENTLY_EMPTY }),
		});
	});
}

async function mockBlockedEmpty(page: import('@playwright/test').Page) {
	await page.route(BLOCKED_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: BLOCKED_EMPTY }),
		});
	});
}

async function mockNeedsPlanningQueue(
	page: import('@playwright/test').Page,
	payload: object,
) {
	await mockNeedsReviewEmpty(page);
	await mockReadyReleaseEmpty(page);
	await mockReleasedRecentlyEmpty(page);
	await mockBlockedEmpty(page);
	await page.route(QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: payload }),
		});
	});
}

const ITEMS_FIXTURE = {
	ok: true,
	queue_key: 'needs_planning',
	total: 2,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=needs-planning',
	items: [
		{
			id: 'DEM-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Works · 98,000,000 KES · Budget linked',
			next_action_label: 'Include in procurement plan',
			primary_action: { label: 'Open', action: 'open_demand', target: 'DEM-001' },
		},
		{
			id: 'DEM-002',
			title: 'Regional Clinic Equipment',
			subtitle: 'Goods · 12,500,000 KES · Budget linked',
			next_action_label: 'Include in procurement plan',
			primary_action: { label: 'Open', action: 'open_demand', target: 'DEM-002' },
		},
	],
};

const EMPTY_FIXTURE = {
	ok: true,
	queue_key: 'needs_planning',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=needs-planning',
	items: [],
};

const VIEW_ALL_FIXTURE = {
	ok: true,
	queue_key: 'needs_planning',
	total: 6,
	limit: 5,
	view_all_href: '/desk/procurement-planning?queue=needs-planning',
	items: Array.from({ length: 5 }, (_, i) => ({
		id: `DEM-V${i + 1}`,
		title: `Demand Item ${i + 1}`,
		subtitle: 'Works · 1,000,000 KES · Budget linked',
		next_action_label: 'Include in procurement plan',
		primary_action: { label: 'Open', action: 'open_demand', target: `DEM-V${i + 1}` },
	})),
};

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/feature content deferred/i,
	/stub content/i,
];

test.describe('P5C-003 Planning Home Needs Planning queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows Needs Planning queue section below summary', async ({ page }) => {
		await mockNeedsPlanningQueue(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-summary')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		const order = await page.evaluate(() => {
			const body = document.querySelector('[data-testid="pp2-planning-home-body"]');
			const summary = document.querySelector('[data-testid="pp2-planning-summary"]');
			const queue = document.querySelector('[data-testid="pp2-queue-needs-planning"]');
			if (!body || !summary || !queue) return null;
			const children = Array.from(body.querySelectorAll('[data-testid="pp2-planning-summary"], [data-testid="pp2-queue-needs-planning"]'));
			return {
				summaryIdx: children.indexOf(summary),
				queueIdx: children.indexOf(queue),
			};
		});
		expect(order).not.toBeNull();
		expect(order!.queueIdx).toBeGreaterThan(order!.summaryIdx);
	});

	test('renders business item cards with Open action', async ({ page }) => {
		await mockNeedsPlanningQueue(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-needs-planning');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(2);
		await expect(section.getByText('District Hospital Renovation Works')).toBeVisible();
		await expect(section.getByText('Works · 98,000,000 KES · Budget linked')).toBeVisible();
		await expect(section.getByText('Next: Include in procurement plan').first()).toBeVisible();
		await expect(section.getByTestId('pp2-home-primary-action')).toHaveCount(2);
	});

	test('shows empty state when queue has no items', async ({ page }) => {
		await mockNeedsPlanningQueue(page, EMPTY_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		await expect(
			page.getByTestId('pp2-queue-needs-planning').getByText('No approved demands need planning.'),
		).toBeVisible();
		await expect(page.getByTestId('pp2-queue-needs-planning').getByTestId('pp2-home-item-card')).toHaveCount(0);
	});

	test('shows View all when total exceeds limit', async ({ page }) => {
		await mockNeedsPlanningQueue(page, VIEW_ALL_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-needs-planning').getByTestId('pp2-home-item-card')).toHaveCount(5);
		const viewAll = page.getByTestId('pp2-queue-needs-planning-view-all');
		await expect(viewAll).toBeVisible();
		await expect(viewAll).toHaveAttribute('href', /procurement-planning\?queue=needs-planning/);
	});

	test('Open keeps user in workbench with item context', async ({ page }) => {
		await mockNeedsPlanningQueue(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		await page
			.getByTestId('pp2-queue-needs-planning')
			.getByTestId('pp2-home-primary-action')
			.first()
			.click();
		await expect(page).toHaveURL(/\/desk\/procurement-planning/, { timeout: 30000 });
		await expect(page).toHaveURL(/queue=needs-planning/);
		await expect(page).toHaveURL(/item=DEM-001/);
	});

	test('does not render handoff cards or forbidden copy', async ({ page }) => {
		await mockNeedsPlanningQueue(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-needs-planning')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-handoff-card')).toHaveCount(0);
		const bodyText = (await page.getByTestId('pp2-planning-home-surface').innerText()) || '';
		for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});
