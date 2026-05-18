/**
 * R8-008 / LV-R8-UI-03 / PLC-SMOKE-UI-003 — Planning Release handoff visible on journey page.
 *
 * Pack §15.2: `plc-handoff-card` for Planning Release Package — source, target, summaries, technical drawer.
 */
import { test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectPlcSmokeUi003PlanningReleaseHandoffCard,
	expectProcurementJourneyPageShell,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('PLC-SMOKE-UI-003 Planning Release handoff (R8-008)', () => {
	test('PLC-SMOKE-UI-003: PKGREL card shows source, target, preview, and technical drawer', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectPlcSmokeUi003PlanningReleaseHandoffCard(page);
	});
});
