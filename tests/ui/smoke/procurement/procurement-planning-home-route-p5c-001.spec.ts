/**
 * P5C-001 — Planning Home dedicated route at /desk/procurement-planning.
 */
import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

const FORBIDDEN_IMPLEMENTATION_COPY = [
	/shell baseline/i,
	/Choose a planning workspace action/i,
	/Open a planning queue from the sidebar/i,
	/feature content deferred/i,
	/stub content/i,
];

test.describe('P5C-001 Planning Home route', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.removeItem('kt-pp2-right-panel-collapsed');
		});
	});

	test('loads canonical Planning Home route with page marker', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-planning-home')).toBeVisible({ timeout: 30000 });
	});

	test('mounts dedicated home surface body', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-planning-home-body')).toBeVisible();
	});

	test('shows Planning Home page header with primary CTA', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-page-header')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-page-title')).toHaveText('Planning Home');
		await expect(page.getByTestId('pp2-page-purpose')).toHaveText(
			/Convert approved demand into tender-ready procurement packages/i
		);
		await expect(page.getByTestId('pp2-page-primary-action')).toBeVisible();
	});

	test('does not mount workbench chrome on Planning Home', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
		await expect(page.getByTestId('pp2-queue-tabs')).toHaveCount(0);
		await expect(page.getByTestId('pp2-primary-work-list-host')).toHaveCount(0);
		await expect(page.getByTestId('pp2-surface-empty-state')).toHaveCount(0);
	});

	test('hides permanent right panel on Planning Home', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-primary-workspace-shell')).toHaveAttribute(
			'data-pp2-home-layout',
			'1',
			{ timeout: 30000 }
		);
		await expect(page.getByTestId('pp2-primary-right-panel')).toBeHidden();
	});

	test('redirects /home alias to canonical root', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/home`, { waitUntil: 'domcontentloaded' });
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
	});

	test('sidebar Workbench link lands on canonical root surface', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning/packages`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-packages-page')).toBeVisible({ timeout: 30000 });
		const planningSection = page.locator('.section-item[title="Procurement Planning"]');
		const workbenchLink = planningSection.locator('.item-anchor', { hasText: 'Workbench' });
		if (!(await workbenchLink.isVisible())) {
			await planningSection.locator('.drop-icon').first().click();
		}
		await expect(workbenchLink).toBeVisible({ timeout: 30000 });
		await workbenchLink.click();
		await expect(page).toHaveURL(/\/desk\/procurement-planning(?:\?|$)/);
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
	});

	test('contains no forbidden implementation copy', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });
		await expect(page.getByTestId('pp2-planning-home-surface')).toBeVisible({ timeout: 30000 });
		const bodyText = await page.locator('body').innerText();
		for (const pattern of FORBIDDEN_IMPLEMENTATION_COPY) {
			expect(bodyText).not.toMatch(pattern);
		}
	});
});
