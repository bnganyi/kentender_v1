/**
 * R5-009 / LV-R5-009-01 — Official STD Library Usage tab shows WORKS PLC journey + linked tender.
 *
 * Depends on seeded WORKS master chain (Administrator).
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

const WORKS_CARD = '[data-testid^="std-library-card-"][aria-label*="KE-PPRA-WORKS-BLDG-2022-04-POC"]';

async function openOfficialLibraryFilteredToWorks(page: Page, root: string) {
	const qs = new URLSearchParams({
		search: 'KE-PPRA-WORKS',
		queue: 'ready_review',
	});
	await page.goto(`${root}/app/std-engine/library?${qs.toString()}`, { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('std-library-page')).toBeVisible({ timeout: 90_000 });
	await expect(page.locator(WORKS_CARD).first()).toBeVisible({ timeout: 90_000 });
}

test.describe('STD Library Usage panel (R5-009)', () => {
	test.describe.configure({ timeout: 120_000 });

	test('PLC-R5-009-01: Usage tab lists WORKS journey JRN-MOH-2026-001 and seeded tender reference', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = baseURL ?? '';
		await openOfficialLibraryFilteredToWorks(page, root);

		await page
			.locator(WORKS_CARD)
			.first()
			.getByRole('button', { name: /View Details/i })
			.click();
		await expect(page.getByTestId('std-library-detail-panel')).toBeVisible({ timeout: 60_000 });
		await page.getByTestId('std-library-tab-usage').click();
		await expect(page.getByTestId('std-library-usage-tab')).toBeVisible({ timeout: 45_000 });

		const journeyPanel = page.getByTestId('std-usage-journey-list');
		await expect(journeyPanel.getByTestId('std-usage-journey-row').first()).toBeVisible({
			timeout: 45_000,
		});
		await expect(journeyPanel).toContainText('JRN-MOH-2026-001');

		const tenderPanel = page.getByTestId('std-usage-tender-list');
		await expect(tenderPanel.getByTestId('std-usage-tender-row').first()).toBeVisible({
			timeout: 45_000,
		});
		await expect(tenderPanel).toContainText('TND-MOH-2026-001');

		const journeyLink = page.getByTestId('std-usage-journey-open-link').first();
		const href = await journeyLink.getAttribute('href');
		expect(href).toContain('/desk/plc-procurement-journey/JRN-MOH-2026-001');
	});

	test('PLC-R5-009-02: Card View Usage jumps to Usage tab with detail loaded', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = baseURL ?? '';
		await openOfficialLibraryFilteredToWorks(page, root);

		await page
			.locator(WORKS_CARD)
			.first()
			.getByRole('button', { name: /View Usage/i })
			.click();

		await expect(page.getByTestId('std-library-usage-tab')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByRole('tab', { name: /Usage/i })).toHaveAttribute('aria-selected', 'true');
	});
});
