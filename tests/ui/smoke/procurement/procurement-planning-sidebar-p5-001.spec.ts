/**
 * P5-001 / PP2-SMOKE-UI-002 — compact Procurement Planning sidebar (five persistent surfaces).
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import { expectPrimarySidebarItemHighlighted } from '../../helpers/workspacePatternContract';

const root = process.env.UI_BASE_URL || 'http://127.0.0.1:8000';

const PP2_SURFACES = [
	{
		label: 'Planning Home',
		testId: 'pp2-planning-home',
		path: '/desk/procurement-planning',
	},
	{
		label: 'Approved Demands',
		testId: 'pp2-approved-demands-page',
		path: '/desk/procurement-planning/approved-demands',
	},
	{
		label: 'Packages',
		testId: 'pp2-package-workbench',
		path: '/desk/procurement-planning/packages',
	},
	{
		label: 'Released to Tender',
		testId: 'pp2-released-to-tender-page',
		path: '/desk/procurement-planning/releases',
	},
	{
		label: 'Planning Evidence',
		testId: 'pp2-planning-evidence-index',
		path: '/desk/procurement-planning/evidence',
	},
] as const;

const FORBIDDEN_SIDEBAR_LABELS = [
	'Readiness Review',
	'Review & Approval',
	'Release to Tender Review',
	'Planning Release Package View',
	'Advanced / Technical Details',
];

async function sidebarLabels(page: import('@playwright/test').Page): Promise<string[]> {
	return page.evaluate(() => {
		const items = Array.from(document.querySelectorAll('.standard-sidebar-item'));
		return items
			.map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
			.filter(Boolean);
	});
}

test.describe('PP2 Planning nested sidebar (P5-001)', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('PP2-SMOKE-UI-002 — sidebar shows exactly five persistent Planning surfaces', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });

		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Procurement Home'))).toBeTruthy();
		expect(labels.some((lab) => lab.includes('Procurement Planning'))).toBeTruthy();
		for (const surface of PP2_SURFACES) {
			expect(labels.some((lab) => lab.includes(surface.label))).toBeTruthy();
		}
		for (const forbidden of FORBIDDEN_SIDEBAR_LABELS) {
			expect(labels.some((lab) => lab.includes(forbidden))).toBeFalsy();
		}
		expect(labels.filter((lab) => PP2_SURFACES.some((s) => lab.includes(s.label))).length).toBeGreaterThanOrEqual(5);
	});

	test('Procurement Planning parent expands and collapses child links', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const parent = page.locator('.section-item[title="Procurement Planning"] .drop-icon').first();
		const child = page.getByRole('link', { name: 'Planning Home' }).first();
		await parent.click();
		await expect(child).toBeVisible();
		await parent.click();
		await expect(child).toBeHidden();
		await parent.click();
		await expect(child).toBeVisible();
	});

	test('Planning subtree has visual hierarchy enhancer classes', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await expect(parentSection).toHaveClass(/kt-pp2-sidebar-parent/);
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible();
		await parentSection.locator('.drop-icon').click();
		for (const surface of PP2_SURFACES) {
			const childLink = page
				.locator('.section-item[title="Procurement Planning"] .nested-container .item-anchor')
				.filter({ hasText: surface.label })
				.first();
			await expect(childLink).toHaveClass(/kt-pp2-sidebar-child/);
		}
	});

	test('first expansion from non-planning route keeps nested indentation', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-home`, { waitUntil: 'domcontentloaded' });
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible();
		const alignment = await page.evaluate(() => {
			const p = document.querySelector('.section-item[title="Procurement Planning"] .sidebar-item-label');
			const h = document.querySelector('.item-anchor[href="/desk/procurement-home"] .sidebar-item-label');
			if (!p || !h) return null;
			return Math.abs(p.getBoundingClientRect().left - h.getBoundingClientRect().left);
		});
		expect(alignment).not.toBeNull();
		expect(alignment as number).toBeLessThanOrEqual(1);
		await parentSection.locator('.drop-icon').click();
		const childLink = parentSection
			.locator('.nested-container .item-anchor')
			.filter({ hasText: 'Planning Home' })
			.first();
		await expect(childLink).toBeVisible();
		await expect(childLink).toHaveClass(/kt-pp2-sidebar-child/);
	});

	test('Procurement Planning icon persists across Procurement route switches', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await page.getByRole('link', { name: 'Budget & Funding' }).first().click();
		await expect(page).toHaveURL(/\/desk\/budget-management/);
		const parentSection = page.locator('.section-item[title="Procurement Planning"]').first();
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible({ timeout: 30000 });

		await page.getByRole('link', { name: 'Tender Management' }).first().click();
		await expect(page).toHaveURL(/\/desk\/tender-management-v2/);
		await expect(parentSection.locator('.kt-pp2-parent-icon')).toBeVisible({ timeout: 30000 });
	});

	test('each sidebar item routes to the correct pp2 surface root', async ({ page }) => {
		for (const surface of PP2_SURFACES) {
			await page.goto(`${root}${surface.path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId(surface.testId)).toBeVisible({ timeout: 30000 });
			await expectPrimarySidebarItemHighlighted(page, surface.label, 'Procurement Planning');
		}
	});

	test('hard refresh keeps Planning sidebar populated', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-package-workbench')).toBeVisible({ timeout: 30000 });
		await page.reload({ waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-package-workbench')).toBeVisible({ timeout: 30000 });

		const bootProbe = await page.evaluate(() => {
			const f = (window as { frappe?: { app?: { sidebar?: { workspace_sidebar_items?: unknown[] } } } })
				.frappe;
			return {
				items_count: f?.app?.sidebar?.workspace_sidebar_items?.length ?? 0,
			};
		});
		expect(bootProbe.items_count).toBeGreaterThan(0);
		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Packages'))).toBeTruthy();
	});
});
