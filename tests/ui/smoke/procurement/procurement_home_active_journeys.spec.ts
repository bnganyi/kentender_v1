/**
 * R4-001 / LV-R4-001-01 / PLC-SMOKE-UI-001 — Procurement Home shows active WORKS journey.
 * Requires WORKS master seed on target site (JRN-MOH-2026-001).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	activeJourneyCard,
	expectProcurementHomeActiveJourneysPanel,
	expectProcurementHomeShell,
	expectProcurementJourneyPageShell,
	expectWorksMasterJourneyHeader,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

const WORKS_JOURNEY_TITLE = 'District Hospital Renovation Works';
const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';
const WORKS_STAGE_LABEL = 'Tender Published';

test.describe('Procurement Home active journeys (R4-001)', () => {
	test('PLC-SMOKE-UI-001: active panel shows WORKS journey with stage and Open Journey', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeShell(page);

		const panel = await expectProcurementHomeActiveJourneysPanel(page);
		const card = activeJourneyCard(page, WORKS_JOURNEY_TITLE);
		await expect(card).toBeVisible({ timeout: 45_000 });
		await expect(card).toContainText(WORKS_STAGE_LABEL);
		await expect(card).toContainText(/next action/i);
		await expect(card).toContainText(/blockers/i);

		const openJourney = card.locator('.plc-home-open-journey').first();
		await expect(openJourney).toBeVisible();
		await openJourney.click();

		await expect(page).toHaveURL(new RegExp(`plc-procurement-journey/${WORKS_JOURNEY_CODE}`), {
			timeout: 45_000,
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expect(page.getByTestId('plc-procurement-journey-placeholder')).toBeVisible({
			timeout: 45_000,
		});
	});

	test('View Evidence navigates to procurement journey route', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeActiveJourneysPanel(page);

		const card = activeJourneyCard(page, WORKS_JOURNEY_TITLE);
		await expect(card).toBeVisible({ timeout: 45_000 });

		const viewEvidence = card.locator('.plc-home-view-evidence').first();
		await expect(viewEvidence).toBeVisible();
		await viewEvidence.click();

		await expect(page).toHaveURL(new RegExp(`plc-procurement-journey/${WORKS_JOURNEY_CODE}`), {
			timeout: 45_000,
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
	});
});
