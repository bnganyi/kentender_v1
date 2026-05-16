/**
 * R4-012 / LV-R4-012-01 — Safe “Open module” deep links (allowlist + tamper resistance).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksJourneyStepCardsSection,
	expectWorksMasterJourneyHeader,
	expectWorksJourneyTimelineSpine,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

const GET_JOURNEY_API =
	'**/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.get_journey';

test.describe('Procurement Journey open module safety (R4-012)', () => {
	test('PLC-R4-012-01: WORKS seed still shows Open module on tender publication', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expectWorksJourneyTimelineSpine(page);
		await expectWorksJourneyStepCardsSection(page);
	});

	test('PLC-R4-012-02: mocked hostile open_module_route (User) renders no Open button', async ({
		page,
	}) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const data = (await res.json()) as {
				message?: { steps?: Array<Record<string, unknown>> };
			};
			const steps = data.message?.steps;
			if (steps?.length) {
				const pub = steps.find((s) => s.step_key === 'tender_publication');
				if (pub) {
					pub.open_module_route = '["Form","User","Administrator"]';
				}
			}
			await route.fulfill({
				status: res.status(),
				contentType: 'application/json',
				body: JSON.stringify(data),
			});
		});

		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);

		const section = page.getByTestId('plc-journey-step-cards');
		await expect(section).toBeVisible({ timeout: 45_000 });

		const tenderPub = section.locator('[data-step-key="tender_publication"]').first();
		await expect(tenderPub.getByTestId('plc-open-current-module')).toHaveCount(0);
	});
});
