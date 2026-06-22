/**
 * P5C-006 — Planning Home Released Recently queue section.
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

const BLOCKED_EMPTY = {
	ok: true,
	queue_key: 'blocked',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=blocked',
	items: [],
};

const RELEASED_ITEMS_FIXTURE = {
	ok: true,
	queue_key: 'released_recently',
	total: 2,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=released-recently',
	items: [
		{
			id: 'PKG-REL-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Released to Tender Management · Tender created',
			next_action_label: 'Continue in Tender Management',
			primary_action: {
				label: 'Open Tender',
				action: 'open_tender',
				target: 'TND-MOH-2026-001',
			},
			secondary_actions: [
				{
					label: 'View Package',
					action: 'open_package',
					target: 'PKG-REL-001',
				},
			],
		},
		{
			id: 'PKG-REL-002',
			title: 'Regional Clinic Equipment Package',
			subtitle: 'Released to Tender Management',
			next_action_label: 'Continue in Tender Management',
			primary_action: {
				label: 'Open Tender',
				action: 'open_tender',
				target: 'PKG-REL-002',
			},
			secondary_actions: [
				{
					label: 'View Package',
					action: 'open_package',
					target: 'PKG-REL-002',
				},
			],
		},
	],
};

const RELEASED_EMPTY_FIXTURE = {
	ok: true,
	queue_key: 'released_recently',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=released-recently',
	items: [],
};

const RELEASED_VIEW_ALL_FIXTURE = {
	ok: true,
	queue_key: 'released_recently',
	total: 6,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=released-recently',
	items: Array.from({ length: 5 }, (_, i) => ({
		id: `PKG-REL-${i + 1}`,
		title: `Released Package ${i + 1}`,
		subtitle: 'Released to Tender Management',
		next_action_label: 'Continue in Tender Management',
		primary_action: {
			label: 'Open Tender',
			action: 'open_tender',
			target: `TND-MOH-2026-${i + 1}`,
		},
		secondary_actions: [
			{
				label: 'View Package',
				action: 'open_package',
				target: `PKG-REL-${i + 1}`,
			},
		],
	})),
};

async function mockHomeQueues(page: import('@playwright/test').Page, releasedPayload: object) {
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
			body: JSON.stringify({ message: releasedPayload }),
		});
	});
	await page.route(BLOCKED_QUEUE_API, async (route) => {
		await route.fulfill({
			status: 200,
			contentType: 'application/json',
			body: JSON.stringify({ message: BLOCKED_EMPTY }),
		});
	});
}

test.describe('P5C-006 Planning Home Released Recently queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows Released Recently queue section below Ready to Release', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-released-recently')).toBeVisible({ timeout: 30000 });
		const order = await page.evaluate(() => {
			const ready = document.querySelector('[data-testid="pp2-queue-ready-release"]');
			const released = document.querySelector('[data-testid="pp2-queue-released-recently"]');
			if (!ready || !released) return null;
			const position = ready.compareDocumentPosition(released);
			return { releasedAfterReady: Boolean(position & Node.DOCUMENT_POSITION_FOLLOWING) };
		});
		expect(order).not.toBeNull();
		expect(order!.releasedAfterReady).toBe(true);
	});

	test('renders released cards with Open Tender and View Package actions', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-released-recently');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(2);
		await expect(section.getByText('District Hospital Renovation Works')).toBeVisible();
		await expect(section.getByText('Released to Tender Management · Tender created')).toBeVisible();
		await expect(section.getByText('Next: Continue in Tender Management').first()).toBeVisible();
		await expect(section.getByTestId('pp2-home-primary-action')).toHaveCount(2);
		await expect(section.getByTestId('pp2-home-secondary-action')).toHaveCount(2);
	});

	test('shows empty state when queue has no items', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_EMPTY_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-released-recently');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(page.getByText('No packages have been released recently.')).toBeVisible();
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(0);
	});

	test('shows View all when total exceeds limit', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_VIEW_ALL_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const section = page.getByTestId('pp2-queue-released-recently');
		await expect(section).toBeVisible({ timeout: 30000 });
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(5);
		const viewAll = page.getByTestId('pp2-queue-released-recently-view-all');
		await expect(viewAll).toBeVisible();
		await expect(viewAll).toHaveAttribute('href', /packages/);
		await expect(viewAll).toHaveAttribute('href', /released-recently/);
	});

	test('Open Tender navigates to tender workspace with context', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await page
			.getByTestId('pp2-queue-released-recently')
			.getByTestId('pp2-home-primary-action')
			.first()
			.click();
		await expect(page).toHaveURL(/\/desk\/tender-management-v2/, { timeout: 30000 });
		await expect(page).toHaveURL(/tender_code=TND-MOH-2026-001/);
	});

	test('View Package navigates to package list with item context', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await page
			.getByTestId('pp2-queue-released-recently')
			.getByTestId('pp2-home-secondary-action')
			.first()
			.click();
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/packages/, { timeout: 30000 });
		await expect(page).toHaveURL(/item=PKG-REL-001/);
		await expect(page).toHaveURL(/queue=released-recently/);
	});

	test('does not render handoff cards in Released Recently section', async ({ page }) => {
		await mockHomeQueues(page, RELEASED_ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-released-recently')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-handoff-card')).toHaveCount(0);
	});
});
