/**
 * P5C-005 — Planning Home Ready to Release queue section.
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

const RELEASED_RECENTLY_EMPTY = {
	ok: true,
	queue_key: 'released_recently',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=released-recently',
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

const ITEMS_FIXTURE = {
	ok: true,
	queue_key: 'ready_to_release',
	total: 2,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=ready-to-release',
	items: [
		{
			id: 'PKG-001',
			title: 'District Hospital Renovation Works',
			subtitle: 'Works · Open Tender · 98,000,000 KES',
			next_action_label: 'Release package',
			primary_action: { label: 'Open', action: 'open_package', target: 'PKG-001' },
		},
		{
			id: 'PKG-002',
			title: 'Regional Clinic Equipment Package',
			subtitle: 'Goods · Restricted Tender · 12,500,000 KES',
			next_action_label: 'Release package',
			primary_action: { label: 'Open', action: 'open_package', target: 'PKG-002' },
		},
	],
};

const EMPTY_FIXTURE = {
	ok: true,
	queue_key: 'ready_to_release',
	total: 0,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=ready-to-release',
	items: [],
};

const VIEW_ALL_FIXTURE = {
	ok: true,
	queue_key: 'ready_to_release',
	total: 6,
	limit: 5,
	view_all_href: '/desk/procurement-planning/packages?queue=ready-to-release',
	items: Array.from({ length: 5 }, (_, i) => ({
		id: `PKG-V${i + 1}`,
		title: `Package Item ${i + 1}`,
		subtitle: 'Works · Open Tender · 1,000,000 KES',
		next_action_label: 'Release package',
		primary_action: { label: 'Open', action: 'open_package', target: `PKG-V${i + 1}` },
	})),
};

async function mockHomeQueues(page: import('@playwright/test').Page, readyPayload: object) {
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
			body: JSON.stringify({ message: readyPayload }),
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
			body: JSON.stringify({ message: BLOCKED_EMPTY }),
		});
	});
}

test.describe('P5C-005 Planning Home Ready to Release queue', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows Ready to Release queue section below Needs Review', async ({ page }) => {
		await mockHomeQueues(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-needs-review')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		const order = await page.evaluate(() => {
			const review = document.querySelector('[data-testid="pp2-queue-needs-review"]');
			const ready = document.querySelector('[data-testid="pp2-queue-ready-release"]');
			if (!review || !ready) return null;
			const position = review.compareDocumentPosition(ready);
			return { readyAfterReview: Boolean(position & Node.DOCUMENT_POSITION_FOLLOWING) };
		});
		expect(order).not.toBeNull();
		expect(order!.readyAfterReview).toBe(true);
	});

	test('renders business item cards with Open action', async ({ page }) => {
		await mockHomeQueues(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		const section = page.getByTestId('pp2-queue-ready-release');
		await expect(section.getByTestId('pp2-home-item-card')).toHaveCount(2);
		await expect(section.getByText('District Hospital Renovation Works')).toBeVisible();
		await expect(section.getByText('Works · Open Tender · 98,000,000 KES')).toBeVisible();
		await expect(section.getByText('Next: Release package').first()).toBeVisible();
		await expect(section.getByTestId('pp2-home-primary-action')).toHaveCount(2);
	});

	test('shows empty state when queue has no items', async ({ page }) => {
		await mockHomeQueues(page, EMPTY_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		await expect(page.getByText('No packages are ready for release.')).toBeVisible();
		await expect(page.getByTestId('pp2-queue-ready-release').getByTestId('pp2-home-item-card')).toHaveCount(
			0,
		);
	});

	test('shows View all when total exceeds limit', async ({ page }) => {
		await mockHomeQueues(page, VIEW_ALL_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-ready-release').getByTestId('pp2-home-item-card')).toHaveCount(
			5,
		);
		const viewAll = page.getByTestId('pp2-queue-ready-release-view-all');
		await expect(viewAll).toBeVisible();
		await expect(viewAll).toHaveAttribute('href', /packages/);
		await expect(viewAll).toHaveAttribute('href', /ready-to-release/);
	});

	test('Open navigates to packages with item context', async ({ page }) => {
		await mockHomeQueues(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		await page
			.getByTestId('pp2-queue-ready-release')
			.getByTestId('pp2-home-primary-action')
			.first()
			.click();
		await expect(page).toHaveURL(/\/desk\/procurement-planning\/packages/, { timeout: 30000 });
		await expect(page).toHaveURL(/item=PKG-001/);
		await expect(page).toHaveURL(/queue=ready-to-release/);
	});

	test('does not render handoff cards in Ready to Release section', async ({ page }) => {
		await mockHomeQueues(page, ITEMS_FIXTURE);
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-ready-release')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-handoff-card')).toHaveCount(0);
	});
});
