import { expect, test } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

function drawerFrame(page) {
	return page.frameLocator('[data-testid="dia-demand-drawer-frame"]');
}

test.describe('DIA demand drawer', () => {
	test('new demand opens in drawer without leaving workspace URL', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);
		const landingUrl = page.url();

		await page.getByTestId('dia-new-demand-button').click();
		await expect(page.getByTestId('dia-demand-drawer')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('dia-landing-page')).toBeVisible();
		const frame = drawerFrame(page);
		await expect(frame.getByTestId('dia-builder-stepper')).toBeVisible({ timeout: 60_000 });
		expect(page.url()).toContain(new URL(landingUrl).pathname);

		await page.getByTestId('dia-demand-drawer-close').click();
		await expect(page.getByTestId('dia-demand-drawer')).toBeHidden({ timeout: 15_000 });
	});
});
