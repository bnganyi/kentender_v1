import { test, expect } from '@playwright/test';
import { loginAsAdministrator } from '../helpers/auth';
import { strategyWorkspace } from '../helpers/selectors';

test('Strategy workspace renders expected shell', async ({ page }) => {
  await loginAsAdministrator(page);

  await page.goto(strategyWorkspace.route);
  await page.waitForLoadState('networkidle');

  await expect(page.getByText(strategyWorkspace.heading).first()).toBeVisible();
  await expect(
    page.getByText(new RegExp(strategyWorkspace.placeholderBlurb, 'i'))
  ).toBeVisible();
});