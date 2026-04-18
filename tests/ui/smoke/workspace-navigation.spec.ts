import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import { budgetWorkspace, procurementWorkspace, strategyWorkspace } from '../helpers/selectors';

async function openWorkspaceByRoute(page, route: string, heading: string) {
  await page.goto(route, { waitUntil: 'domcontentloaded' });
  await page.waitForLoadState('domcontentloaded');
  await expect(page.getByText(heading).first()).toBeVisible();
}

test.describe('Workspace route accessibility', () => {
  test('Strategy Management workspace route opens', async ({ page }) => {
    await loginAsAdministrator(page);
    await openWorkspaceByRoute(page, strategyWorkspace.route, strategyWorkspace.heading);
  });

  test('Budget Management workspace route opens', async ({ page }) => {
    await loginAsAdministrator(page);
    await openWorkspaceByRoute(page, budgetWorkspace.route, budgetWorkspace.heading);
  });

  test('Procurement workspace route opens', async ({ page }) => {
    await loginAsAdministrator(page);
    await openWorkspaceByRoute(page, procurementWorkspace.route, procurementWorkspace.heading);
  });
});