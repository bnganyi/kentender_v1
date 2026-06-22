/**
 * P5B-006 — Shared Planning empty state (surface + future queue copy).
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const WORKBENCH_PATHS = [
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
] as const;

const SURFACE_EMPTY_MESSAGES: Record<string, RegExp> = {
	'/desk/procurement-planning/approved-demands': /No approved demands match this queue/i,
	'/desk/procurement-planning/plans': /No procurement plans match this queue/i,
	'/desk/procurement-planning/packages': /No packages match this queue/i,
	'/desk/procurement-planning/releases': /No released packages match this queue/i,
};

const SURFACE_PURPOSE: Record<string, RegExp> = {
	'/desk/procurement-planning/approved-demands': /Which approved demands can be planned now/i,
	'/desk/procurement-planning/plans': /Which plan owns this procurement work/i,
	'/desk/procurement-planning/packages': /Which packages need work, review, release, or follow-up/i,
	'/desk/procurement-planning/releases': /Which packages have left Planning, and where did they go/i,
};

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
	/feature content deferred/i,
	/stub content/i,
];

test.describe('P5B-006 Planning empty state component', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders pp2-empty-state inside pp2-surface-empty-state on each workbench route', async ({
		page,
	}) => {
		for (const path of WORKBENCH_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			const wrapper = page.getByTestId('pp2-surface-empty-state');
			await expect(wrapper).toBeVisible({ timeout: 30000 });
			await expect(wrapper.getByTestId('pp2-empty-state')).toHaveCount(1);
			await expect(page.getByTestId('pp2-empty-state-message')).toBeVisible();
		}
	});

	test('shows addendum surface empty copy per route', async ({ page }) => {
		for (const [path, pattern] of Object.entries(SURFACE_EMPTY_MESSAGES)) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-empty-state-message')).toHaveText(pattern, {
				timeout: 30000,
			});
		}
	});

	test('does not render surface empty state on Planning Home', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-surface-empty-state')).toHaveCount(0);
	});

	test('keeps page purpose on header separate from empty message on workbench routes', async ({
		page,
	}) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-page-purpose')).toHaveText(
			/Convert approved demand into tender-ready procurement packages/i,
			{ timeout: 30000 }
		);
		for (const [path, purposePattern] of Object.entries(SURFACE_PURPOSE)) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-page-purpose')).toHaveText(purposePattern, {
				timeout: 30000,
			});
			const messagePattern = SURFACE_EMPTY_MESSAGES[path];
			if (messagePattern) {
				await expect(page.getByTestId('pp2-empty-state-message')).toHaveText(messagePattern);
			}
		}
	});

	test('keeps queue tabs, advanced filters, work list, then surface empty state order on packages', async ({
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

	test('workbench routes contain no forbidden implementation copy', async ({ page }) => {
		for (const path of WORKBENCH_PATHS) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-empty-state')).toBeVisible({ timeout: 30000 });
			const bodyText = await page.locator('body').innerText();
			for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});
