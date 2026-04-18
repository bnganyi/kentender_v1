import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import { strategyWorkspace } from '../helpers/selectors';

test('Strategy workspace shell shows actionable entry points', async ({ page }) => {
	await loginAsAdministrator(page);

	await page.goto(strategyWorkspace.route);
	await page.waitForLoadState('networkidle');

	await expect(page.getByText(strategyWorkspace.heading).first()).toBeVisible();
	// Frappe shortcut widgets use role="link" (see shortcut_widget.js), not <button>.
	await expect(page.getByRole('link', { name: 'New Strategic Plan' })).toBeVisible();
	await expect(page.getByText('Strategic Plans', { exact: true }).first()).toBeVisible();
	await expect(page.getByText('Programs', { exact: true }).first()).toBeVisible();
	await expect(page.getByText('Objectives', { exact: true }).first()).toBeVisible();
	await expect(
		page.getByText('No strategic plans yet. Create one to begin.'),
	).toBeVisible();
});
