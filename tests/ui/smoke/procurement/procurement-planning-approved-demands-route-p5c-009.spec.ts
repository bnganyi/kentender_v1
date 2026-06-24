/**
 * P1-007 — Retired Approved Demands route behavior.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/feature content (is )?intentionally deferred/i,
	/shell-only baseline active/i,
	/\bstub content\b/i,
	/technical placeholder/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
	/workflow trace/i,
	/source object/i,
	/target object/i,
	/technical refs/i,
];

test.describe('P1-007 approved-demands retired route', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('approved-demands URL redirects to workbench root', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-approved-demands-page')).toHaveCount(0);
	});

	test('approved-demands queue deep links are preserved on redirected workbench URL', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands?queue=blocked&item=DEM-001`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page).toHaveURL(/\/desk\/procurement-planning\?queue=blocked&item=DEM-001/);
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-approved-demands-page')).toHaveCount(0);
	});

	test('keeps shell and sidebar behavior valid after redirect', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-route-not-found')).toHaveCount(0);
	});

	test('Approved Demands does not appear as persistent Planning sidebar entry', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/plans`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp3-procurement-plans-page')).toBeVisible({ timeout: 30000 });
		const planningSection = page.locator('.section-item[title="Procurement Planning"]');
		const approvedDemandsLink = planningSection.locator('.item-anchor', { hasText: 'Approved Demands' });
		if (!(await approvedDemandsLink.isVisible())) {
			await planningSection.locator('.drop-icon').first().click();
		}
		await expect(approvedDemandsLink).toHaveCount(0);
	});

	test('contains no forbidden implementation or handoff/technical copy', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/approved-demands`, {
			waitUntil: 'domcontentloaded',
		});
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
		const bodyText = await page.locator('body').innerText();
		for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});
