/**
 * P5C-002 — Planning Home summary count bar.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const SUMMARY_FIXTURE = {
	ok: true,
	summary: {
		needs_planning: 1,
		needs_review: 2,
		ready_to_release: 3,
		released_recently: 4,
		blocked: 5,
	},
};

const SUMMARY_LABELS = [
	'Needs Planning',
	'Needs Review',
	'Ready to Release',
	'Released Recently',
	'Blocked',
] as const;

test.describe('P5C-002 Planning Home summary', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('shows planning summary bar on Planning Home', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-summary')).toBeVisible({ timeout: 30000 });
	});

	test('shows all five summary metrics with numeric values', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-summary')).toBeVisible({ timeout: 30000 });
		for (const label of SUMMARY_LABELS) {
			await expect(page.getByTestId('pp2-planning-summary').getByText(label, { exact: false })).toBeVisible();
		}
		await expect(page.getByTestId('pp2-planning-summary-needs-planning')).toBeVisible();
		await expect(page.getByTestId('pp2-planning-summary-needs-review')).toBeVisible();
		await expect(page.getByTestId('pp2-planning-summary-ready-to-release')).toBeVisible();
		await expect(page.getByTestId('pp2-planning-summary-released-recently')).toBeVisible();
		await expect(page.getByTestId('pp2-planning-summary-blocked')).toBeVisible();
	});

	test('places summary above empty queues host inside home body', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-summary')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-home-queues')).toBeAttached();
		const order = await page.evaluate(() => {
			const body = document.querySelector('[data-testid="pp2-planning-home-body"]');
			const summaryHost = body?.querySelector('.pp2-planning-home__summary-host');
			const queues = document.querySelector('[data-testid="pp2-planning-home-queues"]');
			if (!body || !summaryHost || !queues) return null;
			const children = Array.from(body.children);
			return {
				summaryHost: children.indexOf(summaryHost),
				queues: children.indexOf(queues),
			};
		});
		expect(order).not.toBeNull();
		expect(order!.summaryHost).toBeGreaterThanOrEqual(0);
		expect(order!.queues).toBeGreaterThan(order!.summaryHost);
	});

	test('does not mount workbench chrome on Planning Home', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-summary')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp2-work-list')).toHaveCount(0);
		await expect(page.getByTestId('pp2-surface-empty-state')).toHaveCount(0);
	});

	test('renders fixture counts from summary API', async ({ page }) => {
		await page.route('**/api/method/**get_pp_planning_home_summary*', async (route) => {
			await route.fulfill({
				status: 200,
				contentType: 'application/json',
				body: JSON.stringify({ message: SUMMARY_FIXTURE }),
			});
		});
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-summary-needs-planning')).toContainText('1');
		await expect(page.getByTestId('pp2-planning-summary-needs-review')).toContainText('2');
		await expect(page.getByTestId('pp2-planning-summary-ready-to-release')).toContainText('3');
		await expect(page.getByTestId('pp2-planning-summary-released-recently')).toContainText('4');
		await expect(page.getByTestId('pp2-planning-summary-blocked')).toContainText('5');
	});
});
