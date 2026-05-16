import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import { openWorkspaceFromDeskLauncher, desktopModuleTile, dismissOptionalDeskModals } from '../helpers/routes';
import {
	budgetModule,
	procurementModule,
	procurementWorkspace,
	strategyModule,
} from '../helpers/selectors';

// ─── MUST REMAIN — home-grid entry-point contract ────────────────────────────
//
// Strategy and Budget are sub-modules; they must NOT appear as standalone
// home-grid tiles. Access to those workspaces is through deep-link URLs only
// (see workspace-navigation.spec.ts). If these tests start failing it means
// desktop_icon hidden:1 was reverted — fix the JSON fixture, do not change the
// assertions below. See .cursor/rules/kentender-desk-module-tile-policy.mdc.
//
// ─────────────────────────────────────────────────────────────────────────────

test('Procurement opens from module tile then sidebar (not address-bar deep link)', async ({
	page,
}) => {
	await loginAsAdministrator(page);
	await openWorkspaceFromDeskLauncher(page, procurementModule, procurementWorkspace.heading);

	await expect(page.getByText(procurementWorkspace.heading).first()).toBeVisible();
	await expect(page).toHaveURL(/\/(app|desk)\/procurement-home/);
});

test('Strategy tile is NOT present on the home grid (hidden:1 enforced)', async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
	const tile = desktopModuleTile(page, strategyModule);
	await expect(tile).toHaveCount(0);
});

test('Budget tile is NOT present on the home grid (hidden:1 enforced)', async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
	const tile = desktopModuleTile(page, budgetModule);
	await expect(tile).toHaveCount(0);
});