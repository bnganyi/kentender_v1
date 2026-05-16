/**
 * R4-007 / LV-R4-007-01 — Journey lifecycle spine (`plc-journey-timeline`, `plc-journey-step-*`).
 */
import { test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksJourneyTimelineSpine,
	expectWorksMasterJourneyHeader,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('Procurement Journey timeline (R4-007)', () => {
	test('PLC-R4-007-01: WORKS seed shows 12-node spine with pack pillar classes', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expectWorksJourneyTimelineSpine(page);
	});
});
