/**
 * R4-010 / LV-R4-010-01 — Handoff evidence panel (`plc-handoff-panel`, `plc-handoff-card`).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksJourneyHandoffPanel,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

const GET_JOURNEY_API =
	'**/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.get_journey';

test.describe('Procurement Journey handoffs (R4-010)', () => {
	test('PLC-R4-010-01: WORKS seed renders seven handoff cards with pack selectors', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksJourneyHandoffPanel(page);
	});

	test('PLC-R4-010-02: empty handoff list shows placeholder (mocked API)', async ({ page }) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const data = (await res.json()) as { message?: { handoff_cards?: unknown[] } };
			if (data.message) {
				data.message.handoff_cards = [];
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
		await expect(page.getByTestId('plc-handoff-panel-empty')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('plc-handoff-card')).toHaveCount(0);
	});
});
