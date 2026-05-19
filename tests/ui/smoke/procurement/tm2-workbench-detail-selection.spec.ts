/**
 * TM2 workbench — tender selection should not flash the detail panel.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('TM2 workbench tender selection', () => {
	test.setTimeout(180_000);

	test('re-selecting a tender does not wipe detail with Loading and preserves active tab', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		await expect(page.getByTestId('tm2-workbench-page')).toBeVisible({ timeout: 90_000 });

		const allChip = page.getByTestId('tm2-lifecycle-all');
		await expect(allChip).toBeVisible();

		const rows = page.locator('[data-testid="tm2-tender-list-row"]');
		await expect(rows.first()).toBeVisible({ timeout: 60_000 });
		const allText = await allChip.innerText();
		const allMatch = allText.match(/All \((\d+)\)/);
		expect(allMatch).toBeTruthy();
		expect(Number(allMatch?.[1] || 0)).toBeGreaterThan(0);
		const rowCount = await rows.count();
		test.skip(rowCount < 2, 'Need at least two tenders for selection flash regression');

		await rows.first().click();
		await expect(page.locator('[data-testid="tm2-detail-sticky"]')).not.toHaveClass(/d-none/);
		await expect(page.getByTestId('tm2-tender-detail-header')).not.toContainText(/Loading/i, {
			timeout: 60_000,
		});

		await page.getByTestId('tm2-tab-audit').click();
		await expect(page.getByTestId('tm2-tab-audit')).toHaveClass(/active/);

		await rows.first().click();
		await expect(page.getByTestId('tm2-tender-detail-header')).not.toContainText(/Loading/i);
		await expect(page.getByTestId('tm2-tab-audit')).toHaveClass(/active/);

		const secondCode = await rows.nth(1).getAttribute('data-tm2-tender-code');
		expect(secondCode).toBeTruthy();

		const auditPanel = page.locator('[data-testid="tm2-tab-panel-timeline"]');
		await expect(auditPanel).not.toHaveClass(/d-none/);

		await rows.nth(1).click();
		await expect(page.locator('.tm2-detail-is-loading')).toHaveCount(0);
		await expect(page.getByTestId('tm2-tender-detail-header')).toContainText(String(secondCode), {
			timeout: 60_000,
		});
		await expect(page.getByTestId('tm2-tender-detail-header')).not.toContainText(/Loading/i);
		await expect(page.getByTestId('tm2-tab-audit')).toHaveClass(/active/);
		await expect(auditPanel).not.toHaveClass(/d-none/);

		const tabPanelsPadding = await page.locator('[data-testid="tm2-tab-panels"]').evaluate((el) => {
			const style = window.getComputedStyle(el);
			return parseFloat(style.paddingRight || '0');
		});
		expect(tabPanelsPadding).toBeGreaterThanOrEqual(8);
	});
});
