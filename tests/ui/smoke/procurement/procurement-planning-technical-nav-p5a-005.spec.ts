/**
 * P5A-005 — Technical/detail views must not be persistent Planning submenu items.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PP2_ROUTES = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/approved-demands',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/packages',
	'/desk/procurement-planning/releases',
] as const;

const FORBIDDEN_PLANNING_NAV_LABELS = [
	'Planning Inclusion Detail',
	'Release Package Detail',
	'Readiness Review',
	'Review & Approval',
	'Package Lines',
	'Technical Details',
	'Audit Trail',
	'Planning Release Package',
	'Planning Release Package View',
	'Release to Tender Review',
	'Advanced / Technical Details',
	'Planning Evidence',
] as const;

const FORBIDDEN_PLANNING_HREF_SUBSTRINGS = [
	'/procurement-planning/evidence',
	'/procurement-planning/inclusions',
	'/procurement-planning/readiness',
	'/procurement-planning/review',
	'/procurement-planning/lines',
	'/procurement-planning/technical',
	'/procurement-planning/audit',
	'/procurement-planning/releases/',
] as const;

const CANONICAL_PLANNING_CHILD_LABELS = [
	'Planning Home',
	'Approved Demands',
	'Plans',
	'Packages',
	'Released to Tender',
] as const;

async function expandPlanningSubmenu(page: import('@playwright/test').Page): Promise<void> {
	const parent = page.locator('.section-item[title="Procurement Planning"]').first();
	await expect(parent).toBeVisible({ timeout: 30000 });
	const child = page.getByRole('link', { name: 'Planning Home' }).first();
	if (!(await child.isVisible())) {
		await parent.locator('.drop-icon').click();
	}
	await expect(child).toBeVisible();
}

function planningSection(page: import('@playwright/test').Page) {
	return page.locator('.section-item[title="Procurement Planning"]').first();
}

test.describe('P5A-005 Planning technical/detail nav removal', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('forbidden technical/detail labels absent from Planning submenu on all canonical routes', async ({
		page,
	}) => {
		for (const path of PP2_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expandPlanningSubmenu(page);

			const section = planningSection(page);
			for (const label of FORBIDDEN_PLANNING_NAV_LABELS) {
				await expect(section.getByRole('link', { name: label })).toHaveCount(0);
			}

			const labels = await page.evaluate(() => {
				const planningSectionEl = document.querySelector('.section-item[title="Procurement Planning"]');
				if (!planningSectionEl) return [];
				return Array.from(planningSectionEl.querySelectorAll('.sidebar-item-label'))
					.map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
					.filter(Boolean);
			});
			for (const forbidden of FORBIDDEN_PLANNING_NAV_LABELS) {
				expect(labels.some((lab) => lab.includes(forbidden))).toBeFalsy();
			}
		}
	});

	test('Planning nested submenu has exactly five canonical child links', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expandPlanningSubmenu(page);

		const childLabels = await page.evaluate(() => {
			const section = document.querySelector('.section-item[title="Procurement Planning"]');
			if (!section) return [];
			const nested = section.querySelector('.nested-container');
			if (!nested) return [];
			return Array.from(nested.querySelectorAll('.sidebar-item-label'))
				.map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
				.filter(Boolean);
		});
		expect(childLabels).toHaveLength(5);
		for (const label of CANONICAL_PLANNING_CHILD_LABELS) {
			expect(childLabels.some((lab) => lab.includes(label))).toBeTruthy();
		}
	});

	test('forbidden detail hrefs absent from Planning nested submenu', async ({ page }) => {
		for (const path of PP2_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expandPlanningSubmenu(page);

			const section = planningSection(page);
			for (const substring of FORBIDDEN_PLANNING_HREF_SUBSTRINGS) {
				await expect(section.locator(`a.item-anchor[href*="${substring}"]`)).toHaveCount(0);
			}
		}
	});
});
