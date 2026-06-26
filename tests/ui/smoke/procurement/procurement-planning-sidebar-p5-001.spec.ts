/**
 * P1-002 — Procurement Planning sidebar uses single Planning Workbench entry.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import { expectPrimarySidebarItemHighlighted } from '../../helpers/workspacePatternContract';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

async function sidebarLabels(page: import('@playwright/test').Page): Promise<string[]> {
	return page.evaluate(() => {
		const items = Array.from(document.querySelectorAll('.standard-sidebar-item'));
		return items
			.map((el) => (el.textContent || '').replace(/\s+/g, ' ').trim())
			.filter(Boolean);
	});
}

test.describe('P1-002 Planning single-entry sidebar IA', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
	});

	test('sidebar shows only one Planning Workbench entry', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp4-workbench')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp4-nav-planning-workbench')).toHaveCount(1);
		await expect(page.locator('.item-anchor', { hasText: 'Planning Workbench' })).toHaveCount(1);
		await expectPrimarySidebarItemHighlighted(page, 'Planning Workbench', 'Procurement');

		const labels = await sidebarLabels(page);
		expect(labels.some((lab) => lab.includes('Planning Workbench'))).toBeTruthy();
	});

	test('legacy plans and releases routes redirect to root workbench', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(\?.*)?$/);
		await expect(page.getByTestId('pp4-workbench')).toBeVisible({ timeout: 30000 });

		await page.goto(`${root}/desk/procurement-planning/releases`, { waitUntil: 'domcontentloaded' });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(\?.*)?$/);
		await expect(page.getByTestId('pp4-workbench')).toBeVisible({ timeout: 30000 });
	});
});
