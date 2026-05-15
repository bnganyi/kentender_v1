/**
 * G0-012 / LV-G0-017-02 — Procurement module sidebar lifecycle spine (ordering + key routes).
 * G0-017 (b) — general-role spine ordering uses the same contract as Administrator when seed users exist.
 */
import { expect, test } from '@playwright/test';

import {
	loginAsAdministrator,
	loginAsProcurementPlanner,
	loginAsRequisitioner,
} from '../../helpers/auth';
import {
	clickSidebarLink,
	expectProcurementSidebarSpineG012,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

async function tryLogin(fn: () => Promise<void>): Promise<boolean> {
	try {
		await fn();
		return true;
	} catch (e) {
		const msg = e instanceof Error ? e.message : String(e);
		if (msg.includes('Invalid Login')) {
			return false;
		}
		throw e;
	}
}

test.describe('Procurement sidebar G0-012 spine', () => {
	test('Administrator sees ordered spine through Evidence and Configuration heading', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementSidebarSpineG012(page);
	});

	test('Procurement Journeys opens G0-007 placeholder page', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await clickSidebarLink(page, 'Procurement Journeys');
		await expect(page.getByTestId('plc-procurement-journey-placeholder')).toBeVisible({
			timeout: 45_000,
		});
	});

	test('Strategy Alignment opens workspace but keeps Procurement sidebar rail', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await clickSidebarLink(page, 'Strategy Alignment');
		await expect(page).toHaveURL(/strategy-management/i, { timeout: 45_000 });
		const sb = page.locator('.body-sidebar');
		await expect(sb.getByRole('link', { name: 'Procurement Home', exact: true }).first()).toBeVisible({
			timeout: 45_000,
		});
		await expect(sb.getByRole('link', { name: 'Budget & Funding', exact: true }).first()).toBeVisible();
	});

	test('Budget & Funding opens workspace but keeps Procurement sidebar rail', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await clickSidebarLink(page, 'Budget & Funding');
		await expect(page).toHaveURL(/budget-management/i, { timeout: 45_000 });
		const sb = page.locator('.body-sidebar');
		await expect(sb.getByRole('link', { name: 'Procurement Home', exact: true }).first()).toBeVisible({
			timeout: 45_000,
		});
		await expect(sb.getByRole('link', { name: 'Strategy Alignment', exact: true }).first()).toBeVisible();
	});
});

test.describe('Procurement sidebar G0-012 spine — general roles (G0-017)', () => {
	test('Requisitioner sees ordered spine through Evidence and Configuration heading', async ({ page }) => {
		const ok = await tryLogin(() => loginAsRequisitioner(page));
		test.skip(!ok, 'Requisitioner test user not configured on this site');
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementSidebarSpineG012(page, { omitMyWork: true, onlyVisibleSpineLinks: true });
	});

	test('Procurement Planner sees ordered spine through Evidence and Configuration heading', async ({
		page,
	}) => {
		const ok = await tryLogin(() => loginAsProcurementPlanner(page));
		test.skip(!ok, 'Procurement Planner test user not configured on this site');
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementSidebarSpineG012(page, { omitMyWork: true, onlyVisibleSpineLinks: true });
	});
});
