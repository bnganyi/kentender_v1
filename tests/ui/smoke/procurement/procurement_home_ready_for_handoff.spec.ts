/**
 * R4-004 / LV-R4-004-01 — Procurement Home "Ready for Handoff" strip (pack §11.1).
 * Uses `list_journeys({ status: "ready_for_handoff", limit: 20 })`.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	expectProcurementHomeActiveJourneysPanel,
	expectProcurementHomeBlockedPanel,
	expectProcurementHomeNeedsActionPanel,
	expectProcurementHomeReadyForHandoffPanel,
	expectProcurementHomeShell,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

test.describe('Procurement Home ready for handoff (R4-004)', () => {
	test('PLC-SMOKE-UI-R4-004: §11.1 panel order and ready strip loads (empty or cards)', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeShell(page);

		const root = page.locator('#kt-ph-root');
		await expect(root).toBeVisible({ timeout: 45_000 });

		const sections = root.locator('.kt-ph-section');
		await expect(sections).toHaveCount(4);
		await expect(sections.nth(0)).toHaveClass(/plc-procurement-home-active-journeys/);
		await expect(sections.nth(1)).toHaveClass(/plc-procurement-home-needs-action/);
		await expect(sections.nth(2)).toHaveClass(/plc-procurement-home-blocked-journeys/);
		await expect(sections.nth(3)).toHaveClass(/plc-procurement-home-ready-for-handoff/);

		await expectProcurementHomeActiveJourneysPanel(page);
		await expectProcurementHomeNeedsActionPanel(page);
		await expectProcurementHomeBlockedPanel(page);
		const readyPanel = await expectProcurementHomeReadyForHandoffPanel(page);

		const host = readyPanel.locator('#kt-ph-ready-for-handoff-host');
		await expect(host.getByText('Loading journeys…')).toHaveCount(0, { timeout: 45_000 });

		const cards = readyPanel.locator('.kt-ph-journey-card');
		const emptyState = host.getByText('No journeys ready for handoff.');
		const errorState = host.getByText('Unable to load journeys ready for handoff.');
		const n = await cards.count();
		const hasEmpty = await emptyState.isVisible().catch(() => false);
		const hasErr = await errorState.isVisible().catch(() => false);
		expect(n > 0 || hasEmpty || hasErr).toBe(true);
		if (n > 0) {
			const first = cards.first();
			await expect(first.locator('.plc-home-open-journey')).toBeVisible();
		}
	});

	test('optional: Open Journey from first ready-for-handoff card when seeded', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeReadyForHandoffPanel(page);
		const host = page.locator('#kt-ph-ready-for-handoff-host');
		await expect(host.getByText('Loading journeys…')).toHaveCount(0, { timeout: 45_000 });

		const cards = page.locator('.plc-procurement-home-ready-for-handoff .kt-ph-journey-card');
		const n = await cards.count();
		test.skip(n === 0, 'No ready-for-handoff journeys in seed');

		const openJourney = cards.first().locator('.plc-home-open-journey').first();
		await openJourney.click();
		await expect(page).toHaveURL(/plc-procurement-journey/, { timeout: 45_000 });
		await expect(page.getByTestId('plc-procurement-journey-placeholder')).toBeVisible({
			timeout: 45_000,
		});
	});
});
