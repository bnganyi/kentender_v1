import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	clickSidebarLink,
	expectProcurementHomeShell,
	expectProcurementPlanningShell,
	expectSidebarProcurementHomeFirst,
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
	procurementPlanningWorkspace,
} from '../../helpers/procurement';

test.describe('G3 Procurement desk smoke', () => {
	test('Procurement Home shell and quick links route to DIA/PP (no shell hijack)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeShell(page);
		await expect(page).toHaveURL(procurementHomeWorkspace.routePattern);
		await expect(page.getByTestId('dia-landing-page')).toHaveCount(0);
		await expect(page.getByTestId('pp-page-title')).toHaveCount(0);

		await page.getByRole('button', { name: /Open Demand Intake/i }).click();
		await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('dia-page-title')).toContainText('Demand Intake and Approval');

		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectProcurementHomeShell(page);
		await page.getByRole('button', { name: /Open Procurement Planning/i }).click();
		await expectProcurementPlanningShell(page);
		await expect(page).toHaveURL(procurementPlanningWorkspace.routePattern);
	});

	test('DIA and PP shells open from Procurement module sidebar', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectSidebarProcurementHomeFirst(page);

		await clickSidebarLink(page, /Demand Intake/i);
		await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('dia-page-title')).toContainText('Demand Intake and Approval');

		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await clickSidebarLink(page, 'Procurement Planning');
		await expectProcurementPlanningShell(page);
	});

	test('Planning keeps single Procurement sidebar rail', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await clickSidebarLink(page, 'Procurement Planning');
		await expectProcurementPlanningShell(page);

		const homeLinks = page.getByRole('link', { name: 'Procurement Home', exact: true });
		await expect(homeLinks.first()).toBeVisible();
		await expect(homeLinks).toHaveCount(1);
		await expect(page.getByText('Settings', { exact: true }).first()).toBeVisible();
	});

	test('DIA and Settings DocType keep full Procurement sidebar (regression)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expectSidebarProcurementHomeFirst(page);

		await clickSidebarLink(page, /Demand Intake/i);
		await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });
		await expect(page.getByTestId('dia-page-title')).toContainText('Demand Intake and Approval');
		await expectSidebarProcurementHomeFirst(page);

		// Expand Settings (keep_closed=1), then follow the DocType link (same UX as a user).
		const settingsSection = page
			.locator('.body-sidebar .sidebar-item-container.section-item')
			.filter({ hasText: 'Settings' });
		await settingsSection.locator('.standard-sidebar-item').first().click();
		await page
			.locator('.body-sidebar a.item-anchor')
			.filter({ hasText: 'Procurement Templates' })
			.first()
			.click();
		await page.waitForLoadState('domcontentloaded');
		await expect(page).toHaveURL(
			/\/(app|desk)(\/List\/Procurement%20Template|\/procurement-template)/i,
			{ timeout: 45_000 },
		);
		await expectSidebarProcurementHomeFirst(page);
	});
});
