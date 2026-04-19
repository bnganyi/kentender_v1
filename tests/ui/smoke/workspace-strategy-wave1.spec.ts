import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import { strategyWorkspace } from '../helpers/selectors';

test('Strategy workspace shell shows actionable entry points', async ({ page }) => {
	await loginAsAdministrator(page);

	await page.goto(strategyWorkspace.route);
	await page.waitForLoadState('networkidle');

	await expect(page.getByText(strategyWorkspace.heading).first()).toBeVisible();
	await expect(page.getByTestId('strategy-landing-page')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByTestId('strategic-plan-create-button')).toBeVisible();
	await expect(page.getByText('Strategic Plans', { exact: true }).first()).toBeVisible();
	// Empty-state vs populated list depends on site data; do not assert here (see workspace-strategy-master-detail.spec.ts).
});

test('Strategy workspace shell appears after in-app navigation from desk home', async ({ page }) => {
	await loginAsAdministrator(page);

	// Start at desk home (same state as clicking Strategy from the desktop apps grid).
	await page.goto('/desk');
	await page.waitForLoadState('networkidle');

	// Simulate Frappe in-app navigation to the strategy workspace (what the desktop icon does).
	await page.evaluate(() => frappe.set_route('strategy-management'));
	await page.waitForLoadState('networkidle');

	await expect(page.getByText(strategyWorkspace.heading).first()).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('strategy-landing-page')).toBeVisible({ timeout: 60_000 });
	await expect(page.getByText('Strategic Plans', { exact: true }).first()).toBeVisible();
});
