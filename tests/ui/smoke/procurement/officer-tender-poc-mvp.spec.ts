/**
 * Procurement Officer Tender Configuration POC — MVP Desk smoke (doc 9 subset).
 * Requires `procurement.officer@moh.test` from `seed_core_minimal` (see `.env.ui`).
 */
import { expect, test } from '@playwright/test';

import { loginAsProcurementOfficer } from '../../helpers/auth';
import {
	clickOfficerTenderConfigurationAction,
	dismissFrappeMessageIfPresent,
} from '../../helpers/stdAdminConsoleDesk';

test.describe('Procurement Officer Tender Configuration POC — MVP Desk smoke', () => {
	test('OFF-ST-MVP: new tender from POC STD then officer sync + validate', async ({ page }) => {
		test.setTimeout(180_000);
		await loginAsProcurementOfficer(page);
		await page.goto('/app/procurement-tender/new', { waitUntil: 'domcontentloaded' });
		await expect(page.locator('.form-layout').first()).toBeVisible({ timeout: 60_000 });

		const initResp = page.waitForResponse(
			(r) =>
				r.url().includes('initialize_officer_tender_from_template') &&
				r.request().method() === 'POST' &&
				r.status() === 200,
			{ timeout: 120_000 },
		);
		await clickOfficerTenderConfigurationAction(page, 'Start new tender from POC STD');
		await initResp;
		await expect(page).toHaveURL(/procurement-tender\/PT-/);

		const syncResp = page.waitForResponse(
			(r) =>
				r.url().includes('sync_officer_configuration') &&
				r.request().method() === 'POST' &&
				r.status() === 200,
			{ timeout: 120_000 },
		);
		await clickOfficerTenderConfigurationAction(page, 'Sync Configuration');
		await syncResp;

		const valResp = page.waitForResponse(
			(r) =>
				r.url().includes('validate_officer_configuration') &&
				r.request().method() === 'POST' &&
				r.status() === 200,
			{ timeout: 120_000 },
		);
		await clickOfficerTenderConfigurationAction(page, 'Validate (officer)');
		await valResp;

		await dismissFrappeMessageIfPresent(page);
	});
});
