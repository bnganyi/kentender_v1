import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

function drawerFrame(page) {
	return page.frameLocator('[data-testid="dia-demand-drawer-frame"]');
}

/** S2 — New Demand opens the Demand builder in the workspace drawer. */
test('New Demand opens builder with dia-builder-page', async ({ page }) => {
	await loginAsRequisitioner(page);
	await openDIALanding(page);
	const landingUrl = page.url();

	await page.getByTestId('dia-new-demand-button').click();
	await expect(page.getByTestId('dia-demand-drawer')).toBeVisible({ timeout: 60_000 });
	expect(page.url()).toContain(new URL(landingUrl).pathname);

	const frame = drawerFrame(page);
	await expect(frame.getByTestId('dia-builder-page')).toBeVisible({ timeout: 30_000 });
});
