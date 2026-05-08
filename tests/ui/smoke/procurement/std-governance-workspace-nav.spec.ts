/**
 * STD-GOV-NAV-AC-001…008 — Governance & Configuration workspace entry points (Desk).
 *
 * Requires fixtures on site (`Governance & Configuration` Workspace). Administrator has STD Template access.
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator, loginAsProcurementOfficer } from '../../helpers/auth';
import { dismissOptionalDeskModals, openWorkspaceFromDeskLauncher } from '../../helpers/routes';
import { STD_ADMIN_TEMPLATE_CODE } from '../../helpers/stdAdminConsoleDesk';
import { procurementModule } from '../../helpers/selectors';

test.describe('STD Governance workspace navigation', () => {
	test.setTimeout(180_000);

	test('Administrator reaches queues, import, usage, audit, and template form from workspace', async ({
		page,
	}) => {
		await loginAsAdministrator(page);
		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');
		await expect(page.locator('body')).toContainText(/Governance\s*&\s*Configuration/i, {
			timeout: 60_000,
		});
		await expect(page.locator('body')).toContainText(/Official\s+STD\s+Library/i, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(
			/Manage\s+official\s+standard\s+tender\s+documents\s+available\s+for\s+tender\s+preparation/i,
			{ timeout: 30_000 },
		);
		await expect(page.locator('body')).toContainText(
			/PDF\s+or\s+Word\s+files\s+alone\s+do\s+not\s+create\s+a\s+working\s+STD/i,
			{ timeout: 30_000 },
		);
		await expect(page.locator('body')).toContainText(/source\s+evidence/i, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/Run\s+Governance\s+Validation/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/Package\s+validation/i, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/not\s+raw\s+engine\s+traces/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/recombined\s+tender\s+bundle/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/STD-LIB-0300/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/STD-LIB-0310/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/STD-LIB-0250/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/Advanced\s+Technical\s+View/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/not\s+the\s+default\s+path/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/Submission\s+Requirements\s+\(DSM\)/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/Opening\s+Register\s+\(DOM\)/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/Evaluation\s+Rules\s+\(DEM\)/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/Contract\s+Carry-Forward\s+\(DCM\)/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/STD-LIB-0340/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/STD-LIB-0341/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/STD\s+Instances/i, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/not\s+the\s+primary\s+task/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/STD\s+Template\s+Usage\s+shortcut/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/read-only\s+references/i, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/STD-LIB-0320/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/Frappe\s+Desk/i, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/kentender_procurement/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/separate\s+single-page\s+application/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/explicit\s+programme\s+sign-off/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/ISSUES_LOG/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/whitelisted\s+server\s+methods/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/ROLE_STD_ADMIN/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/STD\s+Template\s+Administrator/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/STD\s+Template\s+Importer/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/STD\s+Template\s+Activator/i, {
			timeout: 30_000,
		});
		await expect(page.locator('body')).toContainText(/DocPerm/, { timeout: 30_000 });
		await expect(page.locator('body')).toContainText(/Workstream\s+1/i, { timeout: 30_000 });

		for (const label of [
			'Official STD Library — Catalogue',
			'Import Official STD Package',
			'Pending Validation',
			'Pending Approval',
			'Active STD Templates',
			'Superseded / Retired / Archived',
			'STD Template Usage',
			'STD Governance Audit',
			'STD Package Inspector',
		]) {
			await expect(page.getByRole('link', { name: label }).first()).toBeVisible({ timeout: 30_000 });
		}

		await page.getByRole('link', { name: 'Official STD Library — Catalogue' }).first().click();
		await expect(page).toHaveURL(/std-template|STD%20Template|list/i, { timeout: 45_000 });
		await expect(page.locator('.list-row-head, .frappe-list').first()).toBeVisible({ timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');
		await expect(page.getByRole('link', { name: 'Import Official STD Package' }).first()).toBeVisible({
			timeout: 30_000,
		});

		await page.getByRole('link', { name: 'Import Official STD Package' }).first().click();
		await expect(
			page.locator('.modal-dialog:visible').first().or(page.locator('.form-layout').first()),
		).toBeVisible({ timeout: 45_000 });
		await page.keyboard.press('Escape');

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'Pending Validation' }).first().click();
		await expect(page).toHaveURL(/std-template|STD%20Template|list/i, { timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'Pending Approval' }).first().click();
		await expect(page).toHaveURL(/std-template|STD%20Template|list/i, { timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'Active STD Templates' }).first().click();
		await expect(page).toHaveURL(/std-template|STD%20Template|list/i, { timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'Superseded / Retired / Archived' }).first().click();
		await expect(page).toHaveURL(/std-template|STD%20Template|list/i, { timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'STD Template Usage' }).first().click();
		await expect(page).toHaveURL(/std-template-usage|STD%20Template%20Usage|list/i, { timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'STD Governance Audit' }).first().click();
		await expect(page).toHaveURL(/lifecycle|STD%20Template%20Lifecycle|list/i, { timeout: 45_000 });

		await openWorkspaceFromDeskLauncher(page, procurementModule, 'Governance & Configuration');

		await page.getByRole('link', { name: 'STD Package Inspector' }).first().click();
		await expect(page).toHaveURL(/std-template|STD%20Template|list/i, { timeout: 45_000 });
		const row = page.locator('.list-row, .es-list-row').filter({ hasText: STD_ADMIN_TEMPLATE_CODE }).first();
		await expect(row).toBeVisible({ timeout: 45_000 });
		await row.click();
		await expect(page).toHaveURL(
			new RegExp(`${STD_ADMIN_TEMPLATE_CODE.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}`),
			{ timeout: 60_000 },
		);
	});

	test('Procurement Officer does not see Official STD Library workspace link', async ({ page }) => {
		await loginAsProcurementOfficer(page);
		await page.goto('/app');
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);
		const tile = page.locator('a.desktop-icon[data-id="Procurement"]');
		await tile.waitFor({ state: 'visible', timeout: 45_000 });
		await tile.click();
		await page.waitForLoadState('domcontentloaded');
		await expect(page.getByRole('link', { name: 'Official STD Library', exact: true })).toHaveCount(0);
	});
});
