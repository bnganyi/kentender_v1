import { test, expect } from '@playwright/test';

import { loginAsPlanningAuthority, loginAsRequisitioner, loginAsStrategyManager } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';
import { desktopModuleTile, dismissOptionalDeskModals } from '../../helpers/routes';
import { strategyModule } from '../../helpers/selectors';

test('Strategy Manager sees Strategy landing and mutation actions', async ({ page }) => {
	await loginAsStrategyManager(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('strategic-plan-create-button')).toBeVisible();
	await expect(page.getByTestId('selected-plan-open-builder')).toBeVisible();
	await expect(page.getByTestId('selected-plan-edit-plan')).toBeVisible();
});

test('Planning Authority sees Strategy landing in review mode', async ({ page }) => {
	await loginAsPlanningAuthority(page);
	await openStrategyLanding(page);

	await expect(page.getByTestId('strategic-plan-list')).toBeVisible();
	await expect(page.getByTestId('strategic-plan-create-button')).toHaveCount(0);
	await expect(page.getByTestId('selected-plan-edit-plan')).toHaveCount(0);
	await expect(page.getByTestId('selected-plan-open-builder')).toBeVisible();
});

test('Requisitioner does not see Strategy module on desk home', async ({ page }) => {
	await loginAsRequisitioner(page);
	await page.goto('/app');
	await page.waitForLoadState('networkidle');
	await dismissOptionalDeskModals(page);

	await expect(desktopModuleTile(page, strategyModule)).toHaveCount(0);
});

test('Requisitioner cannot access Strategy landing shell', async ({ page }) => {
	await loginAsRequisitioner(page);
	await page.goto('/desk/strategy-management');
	await page.waitForLoadState('networkidle');

	await expect(page.getByTestId('strategy-landing-page')).toHaveCount(0);
});
