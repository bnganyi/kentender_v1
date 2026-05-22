/**
 * Regression — journey lists belong on Procurement Journeys, not Procurement Home.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('Procurement Home vs Procurement Journeys routing', () => {
	test.setTimeout(120_000);

	test('Procurement Home shows KPI/quick links shell without journey list sections', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/procurement-home`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const landing = page.getByTestId('ph-landing-page');
		await expect(landing).toBeVisible({ timeout: 90_000 });
		await expect(landing.getByTestId('ph-page-title')).toContainText(/Procurement Home/i);
		await expect(landing.getByTestId('plc-procurement-home-active-journeys')).toHaveCount(0);
		await expect(landing.getByText('Quick links')).toBeVisible();
	});

	test('Procurement Journeys page shows active journey list section', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/plc-procurement-journey`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const journeyPage = page.getByTestId('plc-journey-page');
		await expect(journeyPage).toBeVisible({ timeout: 90_000 });
		await expect(page.getByTestId('plc-procurement-journeys-active')).toBeVisible();
		await expect(page.getByTestId('plc-procurement-journeys-needs-action')).toBeVisible();
		await expect(page.getByTestId('plc-procurement-journeys-blocked')).toBeVisible();
		await expect(page.getByTestId('plc-procurement-journeys-ready-for-handoff')).toBeVisible();
	});
});
