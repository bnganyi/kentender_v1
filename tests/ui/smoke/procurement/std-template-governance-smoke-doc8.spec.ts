/**
 * Doc 8 §C — ST-018 (admin UI / state-aware actions) and ST-019 (Procurement Officer boundary).
 *
 * ST-001–ST-017, ST-020: `test_std_template_governance_smoke_doc8.py` (bench).
 * Requires Administrator + seeded `KE-PPRA-WORKS-BLDG-2022-04-POC` (STD-GOV-012).
 * Officer user: `UI_PROCUREMENT_OFFICER_USER` (`.env.ui`).
 *
 * ST-018: Administrator slice only (not full doc 8 multi-role matrix).
 * ST-019 (Desk): direct `/app/std-template/…` blocked — officer tender `std_template` path is
 * covered by `officer-tender-poc-off-st-desk.spec.ts` OFF-ST-002 (same smoke folder; serial run).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator, loginAsProcurementOfficer } from '../../helpers/auth';
import {
	STD_ADMIN_TEMPLATE_CODE,
	closeVisibleHtmlModal,
	expectStdGovernanceGroupVisible,
} from '../../helpers/stdAdminConsoleDesk';

test.describe('STD Template Governance — doc 8 desk smoke (ST-018, ST-019)', () => {
	test.setTimeout(120_000);

	test('ST-018 — Administrator sees governance actions; summary + reasoned dialog', async ({ page }) => {
		await loginAsAdministrator(page);
		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});

		await expectStdGovernanceGroupVisible(page);

		const govGroup = page
			.locator(`.inner-group-button[data-label="${encodeURIComponent('STD Governance')}"]`)
			.first();
		await govGroup.locator('button').first().click();
		await expect(
			page.locator('.dropdown-menu.show a.dropdown-item').filter({ hasText: 'View Governance Summary' }),
		).toBeVisible({ timeout: 15_000 });
		await page.locator('.dropdown-menu.show a.dropdown-item').filter({ hasText: 'View Governance Summary' }).click();
		await closeVisibleHtmlModal(page);

		await govGroup.locator('button').first().click();
		const suspendItem = page.locator('.dropdown-menu.show a.dropdown-item').filter({ hasText: /^Suspend$/ });
		if (await suspendItem.isVisible().catch(() => false)) {
			await suspendItem.click();
			const modal = page.locator('.modal-dialog:visible').first();
			await expect(modal).toBeVisible({ timeout: 30_000 });
			await expect(modal.getByText(/Suspension reason/i)).toBeVisible({ timeout: 15_000 });
			await modal.getByRole('button', { name: /Cancel|Close/i }).first().click();
			await expect(modal).toBeHidden({ timeout: 20_000 });
		}
	});

	test('ST-019 — Procurement Officer cannot open STD Template desk form', async ({ page }) => {
		await loginAsProcurementOfficer(page);
		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});
		// Desk may show Frappe 403 copy *or* "Page … not found" when the role has no workspace/route to the DocType.
		const blocked = page
			.getByText(/not permitted to view this page/i)
			.or(page.getByText(/Page std-template not found/i))
			.or(page.getByRole('heading', { name: /^Not found$/i }));
		await expect(blocked.first()).toBeVisible({ timeout: 90_000 });
		await expect(
			page.locator(`.inner-group-button[data-label="${encodeURIComponent('STD Governance')}"]`),
		).toHaveCount(0);
	});
});
