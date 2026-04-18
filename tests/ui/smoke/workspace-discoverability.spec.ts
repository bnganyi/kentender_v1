import { test, expect, type Page } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import {
	desktopModuleTile,
	dismissOptionalDeskModals,
} from '../helpers/routes';
import {
	budgetModule,
	budgetWorkspace,
	procurementModule,
	procurementWorkspace,
	strategyModule,
	strategyWorkspace,
} from '../helpers/selectors';

async function openDeskHome(page: Page) {
	await page.goto('/app');
	await page.waitForLoadState('domcontentloaded');
	await dismissOptionalDeskModals(page);
}

test.describe('Workspace discoverability from Desk', () => {
	test('Strategy Management is visible from module launcher (no search)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDeskHome(page);

		await expect(desktopModuleTile(page, strategyModule)).toBeVisible({
			timeout: 20_000,
		});
		await desktopModuleTile(page, strategyModule).click();
		await page.waitForLoadState('domcontentloaded');
		await expect(
			page.getByRole('link', { name: strategyWorkspace.heading, exact: true }),
		).toBeVisible();
	});

	test('Budget Management is visible from module launcher (no search)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDeskHome(page);

		await expect(desktopModuleTile(page, budgetModule)).toBeVisible({
			timeout: 20_000,
		});
		await desktopModuleTile(page, budgetModule).click();
		await page.waitForLoadState('domcontentloaded');
		await expect(
			page.getByRole('link', { name: budgetWorkspace.heading, exact: true }),
		).toBeVisible();
	});

	test('Procurement is visible from module launcher (no search)', async ({ page }) => {
		await loginAsAdministrator(page);
		await openDeskHome(page);

		await expect(desktopModuleTile(page, procurementModule)).toBeVisible({
			timeout: 20_000,
		});
		await desktopModuleTile(page, procurementModule).click();
		await page.waitForLoadState('domcontentloaded');
		await expect(
			page.getByRole('link', { name: procurementWorkspace.heading, exact: true }),
		).toBeVisible();
	});
});