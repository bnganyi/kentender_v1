/**
 * §14 G9-002 — Base checkpoint handoff cards on the Journey Desk page: STRATREF, BUDCONF,
 * DEMAPP, PLANINCL, PKGREL, STDREADY, PUBCERT each show route, locked/passed-forward preview,
 * evidence line, Technical details; journey shows **Next action** (Current focus).
 *
 * Depends on WORKS master seed (`JRN-MOH-2026-001`, checkpoint `TENDER_PUBLISHED`).
 */
import { test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectG9BaseHandoffCardsDetail,
	expectProcurementJourneyPageShell,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('G9-002 Base handoff cards visibility', () => {
	test('G9-002: seven base handoff cards show summaries, evidence, and journey next action', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectG9BaseHandoffCardsDetail(page);
	});
});
