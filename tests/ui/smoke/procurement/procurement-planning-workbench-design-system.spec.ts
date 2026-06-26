import { expect, test } from '@playwright/test';
import { loginAsAdministrator } from '../../helpers/auth';

const root =
	(globalThis as { process?: { env?: { UI_BASE_URL?: string } } }).process?.env?.UI_BASE_URL ||
	'http://127.0.0.1:8000';

test.describe('PP3 workbench design system', () => {
	test.beforeEach(async ({ page }) => {
		await loginAsAdministrator(page);
		await page.evaluate(() => {
			window.localStorage.setItem('kt-pp2-right-panel-collapsed', '0');
		});
	});

	test('renders redesigned active plan, queue tabs, cards, and decision panel', async ({ page }) => {
		await page.goto(`${root}/desk/procurement-planning`, { waitUntil: 'domcontentloaded' });

		await expect(page.locator('.pp3-active-plan-card')).toBeVisible();
		await expect(page.locator('.pp3-workbench-queue-tabs__tab')).toHaveCount(6);
		await expect(page.getByTestId('pp3-queue-needs-planning').locator('.pp3-workbench-queue-tabs__count')).toBeVisible();

		const firstRow = page.getByTestId('pp3-work-item-row').first();
		await expect(firstRow).toBeVisible();
		await expect(firstRow.locator('.pp3-work-list__category-pill')).toHaveCount(1);
		await expect(firstRow.locator('.pp3-work-list__status-pill')).toHaveCount(1);

		const rightPanel = page.getByTestId('pp2-primary-right-panel');
		await expect(rightPanel).toBeVisible();
		await expect(rightPanel).toHaveCSS('width', '380px');
		await expect(page.locator('.pp3-selected-work-summary__footer')).toBeVisible();
		await expect(page.getByTestId('pp3-primary-action')).toBeVisible();

		await page.screenshot({ path: 'artifacts/pp3-workbench-design-system.png', fullPage: true });
	});
});

