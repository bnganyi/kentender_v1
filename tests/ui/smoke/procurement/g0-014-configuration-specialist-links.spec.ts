/**
 * G0-014 / LV-G0-014-03 — Configuration exposes full Strategy/Budget workspace links only to specialist roles.
 * LV-G0-017-03 — Administrator: Configuration includes gated specialist links + Official STD Library.
 */
import { expect, test, type Page } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import {
	openProcurementWorkspaceFromModule,
	procurementHomeWorkspace,
} from '../../helpers/procurement';

async function expandProcurementConfigurationSection(page: Page) {
	const configurationSection = page
		.locator('.body-sidebar .sidebar-item-container.section-item')
		.filter({ hasText: 'Configuration' });
	await configurationSection.locator('.standard-sidebar-item').first().click();
}

test.describe('G0-014 Configuration specialist Strategy/Budget links', () => {
	test('Administrator sees Strategy Alignment (full) under Configuration and opens workspace', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expandProcurementConfigurationSection(page);

		const strategyFull = page.getByRole('link', { name: 'Strategy Alignment (full)', exact: true });
		await expect(strategyFull.first()).toBeVisible({ timeout: 45_000 });
		await expect(
			page.locator('.body-sidebar a.item-anchor').filter({ hasText: 'Official STD Library' }).first(),
		).toBeVisible();

		await strategyFull.first().click();
		await page.waitForLoadState('domcontentloaded');
		await expect(page).toHaveURL(/strategy-management/i, { timeout: 45_000 });
	});

	test('Administrator sees Budget & Funding (full) under Configuration and opens workspace', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openProcurementWorkspaceFromModule(page, procurementHomeWorkspace.heading);
		await expandProcurementConfigurationSection(page);

		const budgetFull = page.getByRole('link', { name: 'Budget & Funding (full)', exact: true });
		await expect(budgetFull.first()).toBeVisible({ timeout: 45_000 });
		await budgetFull.first().click();
		await page.waitForLoadState('domcontentloaded');
		await expect(page).toHaveURL(/budget-management/i, { timeout: 45_000 });
	});
});
