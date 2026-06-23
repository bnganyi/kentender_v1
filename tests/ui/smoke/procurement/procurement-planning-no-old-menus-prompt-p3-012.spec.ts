/**
 * P3-012 — Workbench must not push users toward legacy Planning Home / Approved Demands / Packages menus.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';
import {
	mockActivePlan,
	mockWorkbenchItems,
	pp3Root,
	prepareWorkbenchSession,
} from '../../helpers/pp3Workbench';

const LEGACY_PROMPTS = ['Planning Home', 'Approved Demands', 'Go to Packages', 'Open Packages menu'];

const EMPTY_FIXTURE = {
	ok: true,
	queue: 'needs_planning',
	total: 0,
	start: 0,
	limit: 20,
	items: [],
};

test.describe('P3-012 No old menus prompt', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await prepareWorkbenchSession(page);
	});

	test('workbench surface does not expose legacy Planning Home / Approved Demands / Packages prompts', async ({
		page,
	}) => {
		await mockActivePlan(page);
		await mockWorkbenchItems(page, EMPTY_FIXTURE);
		await page.goto(`${pp3Root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('pp2-page-title')).toHaveText('Workbench', { timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-home-surface')).toHaveCount(0);
		await expect(page.getByTestId('pp2-planning-home-queues')).toHaveCount(0);
		await expect(page.getByTestId('pp3-workbench-queue-tabs')).toBeVisible();

		const planningSection = page.locator('.section-item[title="Procurement Planning"]');
		const dropIcon = planningSection.locator('.drop-icon').first();
		if (await dropIcon.isVisible()) {
			await dropIcon.click();
		}
		await expect(planningSection.locator('.item-anchor', { hasText: 'Planning Home' })).toHaveCount(0);
		await expect(planningSection.locator('.item-anchor', { hasText: 'Approved Demands' })).toHaveCount(0);
		await expect(planningSection.locator('.item-anchor', { hasText: /^Packages$/ })).toHaveCount(0);

		const mainText = await page.locator('[data-testid="pp2-primary-main-host"]').innerText();
		for (const prompt of LEGACY_PROMPTS) {
			expect(mainText).not.toContain(prompt);
		}
		await expect(page.getByTestId('pp2-page-primary-action')).toHaveCount(0);

		await page.screenshot({ path: 'artifacts/p3-012-no-old-menus-prompt.png', fullPage: true });
	});
});
