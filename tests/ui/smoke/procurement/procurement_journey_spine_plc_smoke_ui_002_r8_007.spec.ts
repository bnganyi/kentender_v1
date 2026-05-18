/**
 * R8-007 / LV-R8-UI-02 / PLC-SMOKE-UI-002 — Journey Desk page shows full lifecycle spine with statuses.
 *
 * Pack §15.2 selectors (`plc-journey-page`, `plc-journey-step-strategy`, …): implemented as
 * `data-testid` + pillar CSS classes on timeline pills (`procurement_journey_page.js`).
 *
 * Depends on WORKS master seed (`JRN-MOH-2026-001`).
 */
import { test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectPlcSmokeUi002JourneyFullSpine,
	expectProcurementJourneyPageShell,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('PLC-SMOKE-UI-002 journey spine (R8-007)', () => {
	test('PLC-SMOKE-UI-002: journey page renders spine pillars and step statuses', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectPlcSmokeUi002JourneyFullSpine(page);
	});
});
