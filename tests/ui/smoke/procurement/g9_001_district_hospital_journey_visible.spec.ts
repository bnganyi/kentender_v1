/**
 * §14 G9-001 — District Hospital Renovation Works appears as one coherent journey from Strategy
 * through Tender: discoverable from Procurement Home and validated on the Journey Desk page
 * (lifecycle spine + pillar hooks).
 *
 * Depends on WORKS master seed (`JRN-MOH-2026-001`, checkpoint `TENDER_PUBLISHED`).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	activeJourneyCard,
	expectPlcSmokeUi002JourneyFullSpine,
	expectProcurementHomeActiveJourneysPanel,
	expectProcurementHomeShell,
	expectProcurementJourneyPageShell,
	expectWorksMasterJourneyHeader,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

const WORKS_JOURNEY_TITLE = 'District Hospital Renovation Works';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('G9-001 District Hospital journey visibility', () => {
	test('G9-001: Home → Open Journey shows WORKS header and Strategy→Tender spine', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeShell(page);
		await expectProcurementHomeActiveJourneysPanel(page);

		const card = activeJourneyCard(page, WORKS_JOURNEY_TITLE);
		await expect(card).toBeVisible({ timeout: 45_000 });

		await card.getByTestId('plc-home-open-journey').first().click();

		await expect(page).toHaveURL(new RegExp(`plc-procurement-journey/${WORKS_JOURNEY_CODE}`), {
			timeout: 45_000,
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expectPlcSmokeUi002JourneyFullSpine(page);
	});
});
