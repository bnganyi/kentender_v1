/**
 * R4-008 / LV-R4-008-01 — Journey step cards (blocker badges, Open module).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksJourneyStepCardsSection,
	expectWorksJourneyTimelineSpine,
	expectWorksMasterJourneyHeader,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

const GET_JOURNEY_API =
	'**/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.get_journey';

test.describe('Procurement Journey step cards (R4-008)', () => {
	test('PLC-R4-008-01: WORKS seed shows step cards grid + tender open-module link', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expectWorksJourneyTimelineSpine(page);
		await expectWorksJourneyStepCardsSection(page);
	});

	test('PLC-R4-008-02: blocker badge appears when step has blocker_count (mocked API)', async ({ page }) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const data = (await res.json()) as {
				message?: { steps?: Array<Record<string, unknown>> };
			};
			const steps = data.message?.steps;
			if (steps?.length && steps[0]) {
				steps[0] = { ...steps[0], blocker_count: 2 };
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

		const strategyCard = section.locator('[data-step-key="strategy"]').first();
		const badge = strategyCard.getByTestId('plc-journey-step-blocker-badge');
		await expect(badge).toBeVisible();
		await expect(badge).toHaveAttribute('data-blocker-count', '2');
		await expect(badge).toContainText(/2/);
	});
});
