/**
 * TM2 workbench — independent scroll regions (list + detail tab panels).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('TM2 workbench scroll regions', () => {
	test.setTimeout(180_000);

	test('left list and detail tab panels scroll inside the viewport', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('tm2-workbench-page')).toBeVisible({ timeout: 90_000 });

		const listScroll = page.locator('.tm2-tender-list-scroll');
		await expect(listScroll).toBeVisible();

		const rows = page.locator('[data-testid="tm2-tender-list-row"]');
		await expect(rows.first()).toBeVisible({ timeout: 60_000 });
		const rowCount = await rows.count();
		expect(rowCount).toBeGreaterThan(3);

		const listMetrics = await listScroll.evaluate((el) => {
			const style = window.getComputedStyle(el);
			return {
				clientHeight: el.clientHeight,
				scrollHeight: el.scrollHeight,
				overflowY: style.overflowY,
			};
		});
		expect(listMetrics.overflowY).toBe('auto');
		expect(listMetrics.clientHeight).toBeGreaterThan(120);
		expect(listMetrics.scrollHeight).toBeGreaterThan(listMetrics.clientHeight + 8);

		const scrollTopBefore = await listScroll.evaluate((el) => el.scrollTop);
		await listScroll.evaluate((el) => {
			el.scrollTop = 120;
		});
		const scrollTopAfter = await listScroll.evaluate((el) => el.scrollTop);
		expect(scrollTopAfter).toBeGreaterThan(scrollTopBefore);

		const firstRow = page.locator('[data-testid="tm2-tender-list-row"]').first();
		if (await firstRow.count()) {
			await firstRow.click();
			await expect(page.locator('[data-testid="tm2-detail-sticky"]')).not.toHaveClass(/d-none/);
		}

		const tabPanels = page.locator('[data-testid="tm2-tab-panels"]');
		await expect(tabPanels).toBeVisible();

		await page.getByTestId('tm2-tab-preparation').click();

		const panelMetrics = await tabPanels.evaluate((el) => {
			const style = window.getComputedStyle(el);
			return {
				clientHeight: el.clientHeight,
				scrollHeight: el.scrollHeight,
				overflowY: style.overflowY,
			};
		});
		expect(panelMetrics.overflowY).toBe('auto');
		expect(panelMetrics.clientHeight).toBeGreaterThan(120);

		const bodyMetrics = await page.evaluate(() => {
			const body = document.querySelector('#body');
			const main = document.querySelector('.main-section');
			return {
				bodyClientHeight: body ? body.clientHeight : 0,
				bodyScrollHeight: body ? body.scrollHeight : 0,
				mainOverflowY: main ? window.getComputedStyle(main).overflowY : '',
			};
		});
		expect(bodyMetrics.mainOverflowY).toBe('hidden');
		expect(bodyMetrics.bodyScrollHeight).toBeLessThanOrEqual(bodyMetrics.bodyClientHeight + 2);
	});
});
