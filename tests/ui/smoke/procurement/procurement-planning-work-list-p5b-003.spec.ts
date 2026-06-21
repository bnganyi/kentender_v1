/**
 * P5B-003 — Shared Planning work list on canonical surfaces.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const CANONICAL_PATHS = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
] as const;

const PACKAGE_FIXTURE_ITEM = {
	id: 'pkg-moh-2026-001',
	title: 'District Hospital Renovation Works',
	subtitle: 'Works · Open Tender · 98,000,000 KES',
	status_label: 'Released',
	status_tone: 'success',
	blocker_count: 0,
};

const BLOCKED_FIXTURE_ITEM = {
	id: 'pkg-blocked-001',
	title: 'Clinic Equipment Supply',
	subtitle: 'Goods · Restricted Tender · 12,000,000 KES',
	status_label: 'In Review',
	status_tone: 'warning',
	blocker_count: 2,
};

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
];

const FORBIDDEN_ROW_LEAKAGE = [/PLANINCL-/i, /source object/i, /target object/i, /\{"/];

test.describe('P5B-003 Planning work list', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders one work list on each canonical surface', async ({ page }) => {
		for (const path of CANONICAL_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-work-list')).toHaveCount(1, { timeout: 30000 });
			await expect(page.getByTestId('pp2-work-list')).toBeVisible();
		}
	});

	test('shows empty list shell while surface empty message remains', async ({ page }) => {
		for (const path of CANONICAL_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-work-list-empty')).toBeVisible({ timeout: 30000 });
			await expect(page.getByTestId('pp2-empty-state-message')).toBeVisible();
		}
	});

	test('renders queue tabs then advanced filters then work list then surface empty state', async ({
		page,
	}) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-work-list')).toBeVisible({ timeout: 30000 });
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

	test('renders row contract from fixture on packages route', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-work-list')).toBeVisible({ timeout: 30000 });
		await page.evaluate((item) => {
			const host = document.querySelector('[data-testid="pp2-work-list"]');
			const api = (window as unknown as { kentender_procurement?: { PlanningWorkList?: { render: (h: Element, o: object) => void } } })
				.kentender_procurement?.PlanningWorkList;
			if (!host || !api) throw new Error('PlanningWorkList unavailable');
			api.render(host, { items: [item], slug: 'packages' });
		}, PACKAGE_FIXTURE_ITEM);

		const row = page.getByTestId('pp2-work-list-row').first();
		await expect(row).toBeVisible();
		await expect(row.getByTestId('pp2-work-list-row-title')).toHaveText(PACKAGE_FIXTURE_ITEM.title);
		await expect(row.getByTestId('pp2-work-list-row-meta')).toHaveText(PACKAGE_FIXTURE_ITEM.subtitle);
		await expect(row.getByTestId('pp2-work-list-row-status')).toContainText('Released');
		await expect(row.getByTestId('pp2-work-list-row-blocker')).toHaveCount(0);

		const rowText = await row.innerText();
		for (const pattern of FORBIDDEN_ROW_LEAKAGE) {
			expect(rowText).not.toMatch(pattern);
		}
		expect(rowText).not.toContain(PACKAGE_FIXTURE_ITEM.id);
	});

	test('shows blocker marker when blocker_count is greater than zero', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-work-list')).toBeVisible({ timeout: 30000 });
		await page.evaluate((item) => {
			const host = document.querySelector('[data-testid="pp2-work-list"]');
			const api = (window as unknown as { kentender_procurement?: { PlanningWorkList?: { render: (h: Element, o: object) => void } } })
				.kentender_procurement?.PlanningWorkList;
			if (!host || !api) throw new Error('PlanningWorkList unavailable');
			api.render(host, { items: [item], slug: 'packages' });
		}, BLOCKED_FIXTURE_ITEM);

		await expect(page.getByTestId('pp2-work-list-row-blocker')).toHaveText(/2 blockers/i);
	});

	test('updates active row on click and syncs item query param', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-work-list')).toBeVisible({ timeout: 30000 });
		await page.evaluate(
			(items) => {
				const host = document.querySelector('[data-testid="pp2-work-list"]');
				const api = (window as unknown as { kentender_procurement?: { PlanningWorkList?: { render: (h: Element, o: object) => void } } })
					.kentender_procurement?.PlanningWorkList;
				if (!host || !api) throw new Error('PlanningWorkList unavailable');
				api.render(host, { items, slug: 'packages' });
			},
			[PACKAGE_FIXTURE_ITEM, BLOCKED_FIXTURE_ITEM]
		);

		const secondRow = page.getByTestId('pp2-work-list-row').nth(1);
		await secondRow.click();
		await expect(secondRow).toHaveClass(/is-active/);
		await expect(secondRow).toHaveAttribute('aria-selected', 'true');
		await expect(page).toHaveURL(/item=pkg-blocked-001/);
	});

	test('canonical routes contain no forbidden implementation copy', async ({ page }) => {
		for (const path of CANONICAL_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-work-list')).toBeVisible({ timeout: 30000 });
			const bodyText = await page.locator('body').innerText();
			for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});
