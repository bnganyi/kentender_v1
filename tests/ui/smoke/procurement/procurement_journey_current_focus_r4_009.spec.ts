/**
 * R4-009 / LV-R4-009-01 — Current focus panel (`plc-current-focus`) + blockers summary.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementJourneyPageShell,
	expectWorksJourneyCurrentFocusPanel,
	expectWorksJourneyStepCardsSection,
	expectWorksJourneyTimelineSpine,
	expectWorksMasterJourneyHeader,
} from '../../helpers/procurement';

const WORKS_JOURNEY_CODE = 'JRN-MOH-2026-001';

const GET_JOURNEY_API =
	'**/api/method/kentender_procurement.procurement_lifecycle.api.journey_api.get_journey';

test.describe('Procurement Journey current focus (R4-009)', () => {
	test('PLC-R4-009-01: WORKS seed shows focus milestone, journey owner line, empty blocker list', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await page.goto(`/desk/plc-procurement-journey/${WORKS_JOURNEY_CODE}`, {
			waitUntil: 'domcontentloaded',
		});
		await expectProcurementJourneyPageShell(page, WORKS_JOURNEY_CODE);
		await expectWorksMasterJourneyHeader(page);
		await expectWorksJourneyCurrentFocusPanel(page);
		await expectWorksJourneyTimelineSpine(page);
		await expectWorksJourneyStepCardsSection(page);
	});

	test('PLC-R4-009-02: blocker rows render when steps carry blockers (mocked API)', async ({ page }) => {
		await page.route(GET_JOURNEY_API, async (route) => {
			const res = await route.fetch();
			const data = (await res.json()) as {
				message?: {
					steps?: Array<Record<string, unknown> & { step_key?: string }>;
					blocker_count?: number;
					critical_blocker_count?: number;
				};
			};
			const msg = data.message;
			const steps = msg?.steps;
			if (steps?.length) {
				const idx = steps.findIndex((s) => s.step_key === 'tender_closing');
				if (idx >= 0) {
					steps[idx] = {
						...steps[idx],
						blocker_count: 2,
						status_category: 'Blocked',
					};
				}
			}
			if (msg) {
				msg.blocker_count = 2;
				msg.critical_blocker_count = 1;
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

		const panel = page.getByTestId('plc-current-focus');
		await expect(panel).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('plc-current-focus-blocker-total')).toHaveAttribute('data-count', '2');
		await expect(page.getByTestId('plc-current-focus-blocker-critical')).toHaveAttribute('data-count', '1');

		const row = page.locator('[data-testid="plc-current-focus-blocker-row"][data-step-key="tender_closing"]');
		await expect(row).toBeVisible();
		await expect(row).toContainText(/Tender Closed/i);
		await expect(row).toContainText(/2/);
		await expect(page.getByTestId('plc-current-focus-blockers-empty')).toHaveCount(0);
	});
});
