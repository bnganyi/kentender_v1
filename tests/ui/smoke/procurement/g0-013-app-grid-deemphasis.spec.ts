/**
 * G0-013 / LV-G0-013-01–03 — Strategy & Budget home-grid tiles role-gated; Procurement primary for general roles.
 * Feeds LV-G0-017-01 (general user app grid) without closing parent G0-017 alone.
 */
import { expect, test, type Page } from '@playwright/test';

import {
	loginAsPlanningAuthority,
	loginAsProcurementPlanner,
	loginAsRequisitioner,
	loginAsStrategyManager,
} from '../../helpers/auth';
import { desktopModuleTile, dismissOptionalDeskModals } from '../../helpers/routes';
import { budgetModule, procurementModule, strategyModule } from '../../helpers/selectors';

async function openDeskHome(page: Page) {
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
}

test.describe('G0-013 app grid — Strategy & Budget de-emphasis', () => {
	test('Requisitioner: no Strategy/Budget tiles; Procurement primary tile visible', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDeskHome(page);
		await expect(desktopModuleTile(page, strategyModule)).toHaveCount(0);
		await expect(desktopModuleTile(page, budgetModule)).toHaveCount(0);
		await expect(desktopModuleTile(page, procurementModule)).toBeVisible({ timeout: 45_000 });
	});

	test('Procurement Planner: no Strategy/Budget tiles; Procurement present', async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await openDeskHome(page);
		await expect(desktopModuleTile(page, strategyModule)).toHaveCount(0);
		await expect(desktopModuleTile(page, budgetModule)).toHaveCount(0);
		await expect(desktopModuleTile(page, procurementModule)).toBeVisible({ timeout: 45_000 });
	});

	test('Strategy Manager: Strategy tile visible', async ({ page }) => {
		await loginAsStrategyManager(page);
		await openDeskHome(page);
		await expect(desktopModuleTile(page, strategyModule)).toBeVisible({ timeout: 45_000 });
	});

	test('Planning Authority: Budget tile visible; Strategy tile absent (G0-011 Budget specialist)', async ({
		page,
	}) => {
		await loginAsPlanningAuthority(page);
		await openDeskHome(page);
		await expect(desktopModuleTile(page, budgetModule)).toBeVisible({ timeout: 45_000 });
		await expect(desktopModuleTile(page, strategyModule)).toHaveCount(0);
	});
});
