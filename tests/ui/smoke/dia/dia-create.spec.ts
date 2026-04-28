import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/** S2 — New Demand opens the Demand form (builder shell). */
test('New Demand opens builder with dia-builder-page', async ({ page }) => {
	await loginAsRequisitioner(page);
	await openDIALanding(page);
	await page.getByTestId('dia-new-demand-button').click();
	await expect(page).toHaveURL(/\/(app|desk)\/.*demand/i, { timeout: 30_000 });
	await expect(page.getByTestId('dia-builder-page')).toBeVisible({ timeout: 30_000 });
});
