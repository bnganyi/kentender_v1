import { expect, test } from '@playwright/test';

import { collectPortalConsoleErrors, expectNoFrappeDialog, expectNoHorizontalOverflow, waitForPortal } from '../../helpers/portal';

/**
 * BDS-CHG-001 v0.8 plan Phase 2C (BDS8-205) — the portal walking skeleton on
 * BDS-DES-01 Available Tenders, as a signed-out visitor. World-independent:
 * it asserts the shell, the filters, the empty state and the Not found
 * states whatever Tenders the site holds; the fixture-exact DES-01 journey
 * is the Phase 11.1 slice gate.
 */
test.describe('BDS-DES-01 Available Tenders — portal skeleton (guest)', () => {
	test('the shell, filters and empty state render without Desk or the website theme', async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 1440, height: 1024 });
		const response = await page.goto('/tenders', { waitUntil: 'domcontentloaded' });
		expect(response?.status()).toBe(200);
		await waitForPortal(page);
		await expect(page.getByRole('heading', { level: 1, name: 'Available Tenders' })).toBeVisible();
		await expect(page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'Tenders' })).toHaveAttribute('aria-current', 'page');
		await expect(page.locator('#bds-filter-closing')).toHaveValue('open');
		const sheets = await page.evaluate(() => [...document.styleSheets].map((s) => s.href || '').filter(Boolean));
		expect(sheets.filter((href) => !href.includes('/assets/kentender_'))).toEqual([]);
		await expect(page.locator('.navbar, .web-footer, .page-head')).toHaveCount(0);

		// A search nothing matches: the empty state, the URL keeps the filter.
		await page.locator('#bds-filter-search').fill('no tender is called this');
		await expect(page.getByTestId('bds-tenders-empty')).toContainText('No Tenders match these filters.');
		await expect(page).toHaveURL(/\/tenders\?search=no\+tender\+is\+called\+this$/);
		// Direct load of the filtered address restores the same selection.
		await page.reload({ waitUntil: 'domcontentloaded' });
		await waitForPortal(page);
		await expect(page.locator('#bds-filter-search')).toHaveValue('no tender is called this');
		await expect(page.getByTestId('bds-tenders-empty')).toBeVisible();
		await page.getByTestId('bds-tenders-empty').getByRole('button', { name: 'Clear filters' }).click();
		await expect(page).toHaveURL(/\/tenders$/);
		await expect(page.locator('#bds-filter-search')).toHaveValue('');
		await expectNoFrappeDialog(page);
		expect(errors, `page console errors: ${errors.join(' | ')}`).toEqual([]);
	});

	test('every listed Tender links to its public address and the list stacks at 390 px', async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		await page.setViewportSize({ width: 390, height: 844 });
		await page.goto('/tenders?closing=all', { waitUntil: 'domcontentloaded' });
		await waitForPortal(page);
		await expect(page.locator('#bds-filter-closing')).toHaveValue('all');
		await expect(page.getByTestId('bds-tenders-table')).toHaveCount(0);
		const cards = page.locator('[data-testid="bds-tenders-cards"] .bds-card');
		for (const card of await cards.all()) {
			const reference = (await card.locator('.bds-tender-ref').innerText()).trim();
			await expect(card.getByRole('link', { name: 'View Tender' })).toHaveAttribute('href', `/tenders/${reference}`);
		}
		await expectNoHorizontalOverflow(page);
		expect(errors, `page console errors: ${errors.join(' | ')}`).toEqual([]);
	});

	test('a path with no screen is Not found inside the portal, never a Frappe page', async ({ page }) => {
		const errors = collectPortalConsoleErrors(page);
		const tender = await page.goto('/tenders/TND-NOT-A-TENDER', { waitUntil: 'domcontentloaded' });
		expect(tender?.status()).toBe(404);
		await waitForPortal(page);
		await expect(page.getByTestId('bds-state-tender-not-found')).toContainText('Tender not found.');
		await expect(page).toHaveTitle('Tender not found · KenTender');
		await page.getByRole('link', { name: 'Back to Tenders' }).click();
		await expect(page).toHaveURL(/\/tenders$/);
		await expect(page.getByRole('heading', { level: 1, name: 'Available Tenders' })).toBeVisible();

		const bids = await page.goto('/my-bids', { waitUntil: 'domcontentloaded' });
		expect(bids?.status()).toBe(404);
		await expect(page.getByTestId('kt-portal-not-found')).toBeVisible();
		await expect(page.getByRole('navigation', { name: 'Main' }).getByRole('link', { name: 'My bids' })).toHaveAttribute('aria-current', 'page');
		expect(errors, `page console errors: ${errors.join(' | ')}`).toEqual([]);
	});
});
