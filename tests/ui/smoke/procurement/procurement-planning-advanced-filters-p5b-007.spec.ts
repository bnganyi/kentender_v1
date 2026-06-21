/**
 * P5B-007 — Shared Planning advanced filters (collapsed by default).
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const FILTER_SURFACES = [
	{
		path: '/desk/procurement-planning/approved-demands',
		labels: ['Category', 'Funding status', 'Fiscal year'],
	},
	{
		path: '/desk/procurement-planning/plans',
		labels: ['Fiscal year', 'Procuring entity', 'Status'],
	},
	{
		path: '/desk/procurement-planning/packages',
		labels: ['Fiscal year', 'Method', 'Readiness status', 'High-Risk Packages'],
	},
	{
		path: '/desk/procurement-planning/releases',
		labels: ['Fiscal year', 'Procuring entity', 'Tender status'],
	},
] as const;

const PACKAGES_DEFAULT_QUEUE_LABELS = [
	'All',
	'My Work',
	'Needs Review',
	'Ready to Release',
	'Released',
	'Blocked',
] as const;

const PACKAGES_SPECIALIST_CHIP_LABELS = [
	'Draft Packages',
	'High-Risk Packages',
	'Emergency Packages',
	'Procurement Method',
] as const;

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
	/feature content deferred/i,
	/stub content/i,
];

test.describe('P5B-007 Planning advanced filters', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders pp2-advanced-filters on filter-capable surfaces only', async ({ page }) => {
		for (const surface of FILTER_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-advanced-filters')).toHaveCount(1, { timeout: 30000 });
			await expect(page.getByTestId('pp2-advanced-filters')).toBeVisible();
		}
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-advanced-filters')).toHaveCount(0);
	});

	test('keeps advanced filters collapsed by default', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		const details = page.getByTestId('pp2-advanced-filters');
		await expect(details).toBeVisible({ timeout: 30000 });
		await expect(details).not.toHaveAttribute('open', '');
		await expect(page.getByTestId('pp2-advanced-filters-panel')).toBeHidden();
	});

	test('expands to show business filter labels per surface', async ({ page }) => {
		for (const surface of FILTER_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await page.getByTestId('pp2-advanced-filters-toggle').click();
			const panel = page.getByTestId('pp2-advanced-filters-panel');
			await expect(panel).toBeVisible({ timeout: 30000 });
			for (const label of surface.labels) {
				await expect(panel.getByText(label, { exact: true })).toBeVisible();
			}
		}
	});

	test('does not expose specialist filters as default queue chips on packages', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		const tabs = page.getByTestId('pp2-queue-tabs');
		await expect(tabs).toBeVisible({ timeout: 30000 });
		const chips = tabs.locator('[role="tab"]');
		await expect(chips).toHaveCount(PACKAGES_DEFAULT_QUEUE_LABELS.length);
		for (const label of PACKAGES_DEFAULT_QUEUE_LABELS) {
			await expect(chips.filter({ hasText: label })).toHaveCount(1);
		}
		for (const label of PACKAGES_SPECIALIST_CHIP_LABELS) {
			await expect(tabs.getByText(label, { exact: true })).toHaveCount(0);
		}
	});

	test('keeps queue tabs, advanced filters, work list, then surface empty state order', async ({
		page,
	}) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		const order = await page.evaluate(() => {
			const main = document.querySelector('[data-testid="pp2-primary-main-host"]');
			if (!main) return null;
			const queueTabs = main.querySelector('[data-testid="pp2-queue-tabs"]');
			const advanced = main.querySelector('[data-testid="pp2-advanced-filters"]');
			const workList = main.querySelector('[data-testid="pp2-work-list"]');
			const empty = main.querySelector('[data-testid="pp2-surface-empty-state"]');
			if (!queueTabs || !advanced || !workList || !empty) return null;
			const idx = (el: Element | null) => (el ? Array.from(main.querySelectorAll('*')).indexOf(el) : -1);
			return {
				queue: idx(queueTabs),
				advanced: idx(advanced),
				workList: idx(workList),
				empty: idx(empty),
			};
		});
		expect(order).not.toBeNull();
		expect(order!.queue).toBeLessThan(order!.advanced);
		expect(order!.advanced).toBeLessThan(order!.workList);
		expect(order!.workList).toBeLessThan(order!.empty);
	});

	test('filter surfaces contain no forbidden implementation copy', async ({ page }) => {
		for (const surface of FILTER_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-advanced-filters')).toBeVisible({ timeout: 30000 });
			const bodyText = await page.locator('body').innerText();
			for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});
