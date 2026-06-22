/**
 * P5A-004 — Planning Evidence must not be a persistent ordinary Planning submenu item.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const PP3_ROUTES = [
	'/desk/procurement-planning',
	'/desk/procurement-planning/plans',
	'/desk/procurement-planning/releases',
] as const;

async function expandPlanningSubmenu(page: import('@playwright/test').Page): Promise<void> {
	const parent = page.locator('.section-item[title="Procurement Planning"]').first();
	await expect(parent).toBeVisible({ timeout: 30000 });
	const child = page.getByRole('link', { name: 'Workbench' }).first();
	if (!(await child.isVisible())) {
		await parent.locator('.drop-icon').click();
	}
	await expect(child).toBeVisible();
}

test.describe('P5A-004 Planning Evidence nav removal', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('PP2-P5-NG-003 — Planning Evidence absent from Planning submenu on all canonical routes', async ({
		page,
	}) => {
		for (const path of PP3_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expandPlanningSubmenu(page);

			const planningSection = page.locator('.section-item[title="Procurement Planning"]').first();
			await expect(planningSection.getByRole('link', { name: 'Planning Evidence' })).toHaveCount(0);
			await expect(
				planningSection.locator('a.item-anchor[href*="/procurement-planning/evidence"]'),
			).toHaveCount(0);

			const labels = await page.evaluate(() => {
				const section = document.querySelector('.section-item[title="Procurement Planning"]');
				if (!section) return [];
				return Array.from(section.querySelectorAll('.sidebar-item-label'))
					.map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
					.filter(Boolean);
			});
			expect(labels.some((lab) => lab.includes('Planning Evidence'))).toBeFalsy();
		}
	});

	test('no planning evidence index surface mounted by default', async ({ page }) => {
		for (const path of PP3_ROUTES) {
			await page.goto(`${root}${path}`, { waitUntil: 'domcontentloaded' });
			await expect(page.getByTestId('pp2-planning-evidence-index')).toHaveCount(0);
		}
	});
});
