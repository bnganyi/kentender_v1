/**
 * R4-011 / LV-R4-011-01 — Evidence timeline (`plc-evidence-timeline`, pack §9.5).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksJourneyEvidenceTimeline,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

const GET_JOURNEY_API =
	'**/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.get_journey';

test.describe('Procurement Journey evidence timeline (R4-011)', () => {
	test('PLC-R4-011-01: WORKS seed shows seven §9.5 evidence events in order', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksJourneyEvidenceTimeline(page);
	});

	test('PLC-R4-011-02: empty evidence_summary shows placeholder (mocked API)', async ({ page }) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const data = (await res.json()) as { message?: { evidence_summary?: unknown[] } };
			if (data.message) {
				data.message.evidence_summary = [];
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
		await expect(page.getByTestId('plc-evidence-timeline-empty')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('plc-evidence-timeline-event')).toHaveCount(0);
	});
});
