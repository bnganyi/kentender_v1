/**
 * R4-013 / LV-R4-013-01 — Technical evidence drawer (`plc-technical-evidence-drawer`).
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

test.describe('Procurement Journey technical evidence drawer (R4-013)', () => {
	test('PLC-R4-013-01: STRATREF Technical details opens modal with JSON body', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksJourneyHandoffPanel(page);

		const panel = page.getByTestId('plc-handoff-panel');
		const strat = panel.locator('[data-handoff-code="STRATREF-MOH-2026-001"]').first();
		await strat.getByTestId('plc-open-evidence').click();

		const drawer = page.getByTestId('plc-technical-evidence-drawer');
		await expect(drawer).toBeVisible({ timeout: 15_000 });
		await expect(page.getByTestId('plc-technical-evidence-handoff-code')).toContainText(
			'STRATREF-MOH-2026-001',
		);
		await expect(page.getByTestId('plc-technical-evidence-body')).toContainText('programme_code');
		await expect(page.getByTestId('plc-technical-evidence-body')).toContainText('PROG-MOH-INFRA');

		await drawer.locator('[data-dismiss="modal"]').first().click();
		await expect(drawer).toBeHidden();
	});

	test('PLC-R4-013-02: when all handoffs lack technical_refs, no Technical details buttons', async ({
		page,
	}) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const data = (await res.json()) as {
				message?: { handoff_cards?: Array<Record<string, unknown>> };
			};
			const cards = data.message?.handoff_cards;
			if (cards?.length) {
				for (let i = 0; i < cards.length; i += 1) {
					cards[i] = { ...cards[i], technical_refs: {} };
				}
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

		await expect(page.getByTestId('plc-open-evidence')).toHaveCount(0);
	});
});
