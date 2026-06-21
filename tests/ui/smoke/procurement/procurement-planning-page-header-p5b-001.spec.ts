/**
 * P5B-001 — Shared Planning page header on canonical surfaces.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const CANONICAL_SURFACES = [
	{
		path: '/desk/procurement-planning',
		title: 'Planning Home',
		purpose: /Convert approved demand into tender-ready procurement packages/i,
		hasPrimary: true,
	},
	{
		path: '/desk/procurement-planning/approved-demands',
		title: 'Approved Demands',
		purpose: /Which approved demands can be planned now/i,
		hasPrimary: false,
	},
	{
		path: '/desk/procurement-planning/plans',
		title: 'Plans',
		purpose: /Which plan owns this procurement work/i,
		hasPrimary: false,
	},
	{
		path: '/desk/procurement-planning/packages',
		title: 'Packages',
		purpose: /Which packages need work, review, release, or follow-up/i,
		hasPrimary: false,
	},
	{
		path: '/desk/procurement-planning/releases',
		title: 'Released to Tender',
		purpose: /Which packages have left Planning, and where did they go/i,
		hasPrimary: false,
	},
] as const;

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
];

test.describe('P5B-001 Planning page header', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('renders one page header on each canonical surface', async ({ page }) => {
		for (const surface of CANONICAL_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-page-header')).toHaveCount(1, { timeout: 30000 });
			await expect(page.getByTestId('pp2-page-header')).toBeVisible();
		}
	});

	test('shows title and purpose per surface', async ({ page }) => {
		for (const surface of CANONICAL_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-page-title')).toHaveText(surface.title, { timeout: 30000 });
			await expect(page.getByTestId('pp2-page-purpose')).toHaveText(surface.purpose);
		}
	});

	test('shows home primary action only on Planning Home', async ({ page }) => {
		for (const surface of CANONICAL_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
			if (surface.hasPrimary) {
				await expect(page.getByTestId('pp2-page-primary-action')).toHaveCount(1);
				await expect(page.getByTestId('pp2-page-primary-action')).toHaveText(
					/New package from approved demand/i
				);
			} else {
				await expect(page.getByTestId('pp2-page-primary-action')).toHaveCount(0);
			}
		}
	});

	test('empty state shows message only without duplicated title or purpose', async ({ page }) => {
		for (const surface of CANONICAL_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			const emptyState = page.getByTestId('pp2-surface-empty-state');
			await expect(emptyState).toBeVisible({ timeout: 30000 });
			await expect(emptyState.getByTestId('pp2-page-title')).toHaveCount(0);
			await expect(emptyState.getByTestId('pp2-page-purpose')).toHaveCount(0);
			await expect(page.getByTestId('pp2-empty-state-message')).toBeVisible();
		}
	});

	test('canonical routes contain no forbidden implementation copy', async ({ page }) => {
		for (const surface of CANONICAL_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-page-header')).toBeVisible({ timeout: 30000 });
			const bodyText = await page.locator('body').innerText();
			for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
				expect(bodyText).not.toMatch(pattern);
			}
		}
	});
});
