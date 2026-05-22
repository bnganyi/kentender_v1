import { test, expect } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { openStrategyLanding } from '../../helpers/strategyLanding';

test('Audit tab shows downstream usage section', async ({ page }) => {
	await loginAsAdministrator(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategy-tab-audit').click();
	await expect(page.getByTestId('strategy-audit-panel')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('strategy-downstream-usage')).toBeVisible();
});

test('Structure tab does not show procurement impact by default', async ({ page }) => {
	await loginAsAdministrator(page);
	await openStrategyLanding(page);

	await page.getByTestId('strategy-tab-structure').click();
	await expect(page.getByTestId('strategy-structure-panel')).toBeVisible({ timeout: 30_000 });
	await expect(page.getByTestId('plc-strategy-procurement-journey-impact')).toHaveCount(0);
});
