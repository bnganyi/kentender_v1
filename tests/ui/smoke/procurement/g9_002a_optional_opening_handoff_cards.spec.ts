/**
 * §14 G9-002A — Optional opening handoff cards (**CLOSECERT**, **OPENREADY**):
 *
 * - **Branch A:** On **`TENDER_PUBLISHED`**-only sites, both cards must **not** appear on the journey handoff panel.
 * - **Branch B:** When **`OPENING_READY`** seed created both DocTypes (`plcOpeningCheckpointHandoffsSeeded`), both cards **must** render with summaries + evidence + Technical details.
 *
 * Exactly one branch runs per site (the other `test.skip`s). Matches **R8-016** / **R5-011-02** conditional discipline.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectG9OpeningCheckpointHandoffCards,
	expectProcurementJourneyPageShell,
	plcOpeningCheckpointHandoffsSeeded,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

test.describe('G9-002A Optional opening handoff cards', () => {
	test('G9-002A-a: CLOSECERT and OPENREADY absent when OPENING_READY not seeded', async ({ page }) => {
		await loginAsAdministrator(page);
		const openingSeeded = await plcOpeningCheckpointHandoffsSeeded(page);
		test.skip(
			openingSeeded,
			'OPENING_READY handoffs present — G9-002A-b covers visibility.',
		);

		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);

		const panel = page.getByTestId('plc-handoff-panel');
		await expect(panel).toBeVisible({ timeout: 45_000 });
		await expect(panel.locator('[data-handoff-code="CLOSECERT-TND-MOH-2026-001"]')).toHaveCount(0);
		await expect(panel.locator('[data-handoff-code="OPENREADY-TND-MOH-2026-001"]')).toHaveCount(0);
	});

	test('G9-002A-b: CLOSECERT and OPENREADY visible when OPENING_READY checkpoint seeded', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		const openingSeeded = await plcOpeningCheckpointHandoffsSeeded(page);
		test.skip(
			!openingSeeded,
			'OPENING_READY handoffs not on site — load `load_procurement_lifecycle_works_master(checkpoint="OPENING_READY")` to exercise this branch.',
		);

		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectG9OpeningCheckpointHandoffCards(page);
	});
});
