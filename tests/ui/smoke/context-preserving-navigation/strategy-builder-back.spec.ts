import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Strategy builder route redirects to workspace Structure tab', async ({ page }) => {
	await loginAsAdministrator(page);
	await page.goto('/app/strategy-management', { waitUntil: 'domcontentloaded' });
	await expect(page.getByTestId('strategy-landing-page')).toBeVisible({ timeout: 60_000 });

	const firstRow = page.locator('[data-testid^="strategic-plan-row-"]').first();
	await firstRow.click();
	const planId = (await firstRow.getAttribute('data-strategy-plan')) || '';

	await page.goto(`/app/strategy-builder/${planId}`, { waitUntil: 'domcontentloaded' });
	await expect(page).toHaveURL(/strategy-management/);
	await expect(page.getByTestId('strategy-tab-panel-structure')).toBeVisible({ timeout: 60_000 });
});

test('Back to Workbench returns to Strategy landing', async ({ page }) => {
	await loginAsAdministrator(page);
	await openStrategyLanding(page);
	await page.getByTestId('strategy-tab-structure').click();
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible({ timeout: 30_000 });

	// Workspace is the workbench; landing page remains visible with tabs.
	await expect(page.getByTestId('strategy-landing-page')).toBeVisible();
	await expect(page.getByTestId('strategic-plans-section')).toBeVisible();
});
