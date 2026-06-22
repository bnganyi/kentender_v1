/**
 * P5C-007 — Planning Home Blocked queue section.
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

const NEEDS_PLANNING_EMPTY = {
	ok: true,
	queue_key: 'needs_planning',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/approved-demands',
	items: [],
};

const NEEDS_REVIEW_EMPTY = {
	ok: true,
	queue_key: 'needs_review',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=needs-review',
	items: [],
};

const READY_RELEASE_EMPTY = {
	ok: true,
	queue_key: 'ready_to_release',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=ready-to-release',
	items: [],
};

const RELEASED_RECENTLY_EMPTY = {
	ok: true,
	queue_key: 'released_recently',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=released-recently',
	items: [],
};

const BLOCKED_ITEMS_FIXTURE = {
	ok: true,
	queue_key: 'blocked',
	total: 2,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=blocked',
	items: [
		{
			id: 'DEM-BLK-001',
			title: 'District Hospital Renovation Works Demand',
			subtitle: 'Works · 98,000,000 KES · Missing approved budget link',
			next_action_label: 'Resolve blocker',
			primary_action: {
				label: 'Resolve blocker',
				action: 'open_demand',
				target: 'DEM-BLK-001',
			},
		},
		{
			id: 'PKG-BLK-001',
			title: 'Regional Clinic Equipment Package',
			subtitle: 'Goods · Open Tender · 12,500,000 KES · Readiness checks failed',
			next_action_label: 'Resolve blocker',
			primary_action: {
				label: 'Resolve blocker',
				action: 'open_package',
				target: 'PKG-BLK-001',
			},
		},
	],
};

const BLOCKED_EMPTY_FIXTURE = {
	ok: true,
	queue_key: 'blocked',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=blocked',
	items: [],
};

const BLOCKED_VIEW_ALL_FIXTURE = {
	ok: true,
	queue_key: 'blocked',
	total: 7,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=blocked',
	items: Array.from({ length: 5 }, (_, i) => ({
		id: `PKG-BLK-${i + 1}`,
		title: `Blocked Package ${i + 1}`,
		subtitle: 'Works · Open Tender · 1,000,000 KES · Readiness checks failed',
		next_action_label: 'Resolve blocker',
		primary_action: {
			label: 'Resolve blocker',
			action: 'open_package',
			target: `PKG-BLK-${i + 1}`,
		},
	})),
};

async function mockHomeQueues(page: import('@playwright/test').Page, blockedPayload: object) {
	await page.route(NEEDS_PLANNING_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NEEDS_PLANNING_EMPTY }),
		});
	});
	await page.route(NEEDS_REVIEW_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: NEEDS_REVIEW_EMPTY }),
		});
	});
	await page.route(READY_RELEASE_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: READY_RELEASE_EMPTY }),
		});
	});
	await page.route(RELEASED_RECENTLY_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: RELEASED_RECENTLY_EMPTY }),
		});
	});
	await page.route(BLOCKED_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: blockedPayload }),
		});
	});
}

test.describe('P5C-007 Planning Home Blocked queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows Blocked queue section below Released Recently', async ({ page }) => {
		await mockHomeQueues(page, BLOCKED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-released-recently')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-blocked')).toBeVisible({ timeout: 30000 });
		const order = await page.evaluate(() => {
			const released = document.querySelector('[data-testid="pp2-queue-released-recently"]');
			const blocked = document.querySelector('[data-testid="pp2-queue-blocked"]');
			if (!released || !blocked) return null;
			const position = released.compareDocumentPosition(blocked);
			return { blockedAfterReleased: Boolean(position & Node.DOCUMENT_POSITION_FOLLOWING) };
		});
		expect(order).not.toBeNull();
		expect(order!.blockedAfterReleased).toBe(true);
	});

	test('renders blocked cards in concise business language', async ({ page }) => {
		await mockHomeQueues(page, BLOCKED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-blocked');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(2);
		await expect(section.getByText('District Hospital Renovation Works Demand')).toBeVisible();
		await expect(section.getByText('Missing approved budget link')).toBeVisible();
		await expect(section.getByText('Next: Resolve blocker').first()).toBeVisible();
		await expect(section.getByTestId('pp2-home-primary-action')).toHaveCount(2);
	});

	test('shows empty state when blocked queue has no items', async ({ page }) => {
		await mockHomeQueues(page, BLOCKED_EMPTY_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-blocked');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(page.getByText('No planning blockers found.')).toBeVisible();
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(0);
	});

	test('shows View all when blocked total exceeds limit', async ({ page }) => {
		await mockHomeQueues(page, BLOCKED_VIEW_ALL_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-blocked');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(5);
		const viewAll = page.getByTestId('pp2-queue-blocked-view-all');
		await expect(viewAll).toBeVisible();
		await expect(viewAll).toHaveAttribute('href', /packages/);
		await expect(viewAll).toHaveAttribute('href', /queue=blocked/);
	});

	test('Resolve blocker on demand navigates to approved demands with context', async ({ page }) => {
		await mockHomeQueues(page, BLOCKED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await page
			.getByTestId('pp2-queue-blocked')
			.getByTestId('pp2-home-primary-action')
			.first()
			.click();
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/approved-demands/, { timeout: 30000 });
		await expect(page).toHaveURL(/item=DEM-BLK-001/);
		await expect(page).toHaveURL(/queue=blocked/);
	});

	test('does not render handoff cards in Blocked section', async ({ page }) => {
		await mockHomeQueues(page, BLOCKED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-blocked')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-handoff-card')).toHaveCount(0);
	});
});
