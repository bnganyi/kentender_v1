/**
 * P5B-002 — Shared Planning queue tabs on canonical surfaces.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const WORKBENCH_SURFACE_PATHS = [
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
] as const;

const SURFACE_QUEUE_CONFIG = [
	{
		path: '/desk/procurement-planning/approved-demands',
		labels: ['Ready to Plan', 'Blocked', 'Already Planned'],
	},
	{
		path: '/desk/procurement-planning/packages',
		labels: ['All', 'My Work', 'Needs Review', 'Ready to Release', 'Released', 'Blocked'],
	},
	{
		path: '/desk/procurement-planning/releases',
		labels: ['All', 'Released'],
	},
] as const;

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
];

function queueTabLocator(page: import('@playwright/test').Page, id: string) {
	return page.getByTestId(`pp2-queue-tab-${id}`);
}

test.describe('P5B-002 Planning queue tabs', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders one queue tab bar on each workbench surface', async ({ page }) => {
		for (const path of WORKBENCH_SURFACE_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(1, { timeout: 30000 });
			await expect(page.getByTestId('pp2-queue-tabs')).toBeVisible();
		}
	});

	test('shows at most six queue chips per surface with expected labels', async ({ page }) => {
		for (const surface of SURFACE_QUEUE_CONFIG) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const tabs = page.getByTestId('pp2-queue-tabs');
			await expect(tabs).toBeVisible({ timeout: 30000 });
			const chips = tabs.locator('[role="tab"]');
			await expect(chips).toHaveCount(surface.labels.length);
			expect(surface.labels.length).toBeLessThanOrEqual(6);
			for (const label of surface.labels) {
				await expect(chips.filter({ hasText: label })).toHaveCount(1);
			}
		}
	});

	test('selects first chip by default with active state', async ({ page }) => {
		for (const surface of SURFACE_QUEUE_CONFIG) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const tabs = page.getByTestId('pp2-queue-tabs');
			await expect(tabs).toBeVisible({ timeout: 30000 });
			const firstChip = tabs.locator('[role="tab"]').first();
			await expect(firstChip).toHaveClass(/is-active/);
			await expect(firstChip).toHaveAttribute('aria-selected', 'true');
		}
	});

	test('updates active chip on click', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-tabs')).toBeVisible({ timeout: 30000 });
		const secondChip = queueTabLocator(page, 'my-work');
		await secondChip.click();
		await expect(secondChip).toHaveClass(/is-active/);
		await expect(secondChip).toHaveAttribute('aria-selected', 'true');
		const firstChip = queueTabLocator(page, 'all');
		await expect(firstChip).not.toHaveClass(/is-active/);
		await expect(firstChip).toHaveAttribute('aria-selected', 'false');
	});

	test('does not render queue tabs on Workbench root', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-planning-workbench')).toHaveCount(1, { timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(0);
	});

	test('does not render queue tabs on Procurement Plans setup surface', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-procurement-plans-page')).toHaveCount(1, { timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toHaveCount(0);
	});

	test('syncs queue selection to URL query param on packages', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-tabs')).toBeVisible({ timeout: 30000 });
		await queueTabLocator(page, 'needs-review').click();
		await expect(page).toHaveURL(/queue=needs-review/);
	});

	test('renders queue tabs before empty state in main host', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-queue-tabs')).toBeVisible({ timeout: 30000 });
		const order = await page.evaluate(() => {
			const main = document.querySelector('[data-testid="pp2-primary-main-host"]');
			if (!main) return null;
			const queueHost = main.querySelector('[data-testid="pp2-primary-queue-host"]');
			const empty = main.querySelector('[data-testid="pp2-surface-empty-state"]');
			if (!queueHost || !empty) return null;
			const nodes = Array.from(main.children);
			const contentIndex = nodes.findIndex(
				(node) => node.contains(empty) || node === empty.parentElement
			);
			return {
				queueIndex: nodes.indexOf(queueHost),
				contentIndex,
			};
		});
		expect(order).not.toBeNull();
		expect(order!.queueIndex).toBeGreaterThanOrEqual(0);
		expect(order!.contentIndex).toBeGreaterThanOrEqual(0);
		expect(order!.queueIndex).toBeLessThan(order!.contentIndex);
	});

	test('canonical routes contain no forbidden implementation copy', async ({ page }) => {
		for (const surface of SURFACE_QUEUE_CONFIG) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-queue-tabs')).toBeVisible({ timeout: 30000 });
			const bodyText = await page.locator('body').innerText();
			for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});
