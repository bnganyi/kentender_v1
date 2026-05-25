import { expect, test } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

function drawerFrame(page) {
	return page.frameLocator('[data-testid="dia-demand-drawer-frame"]');
}

test.describe('DIA form context preservation', () => {
	test('new demand drawer keeps workspace visible and procurement sidebar', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);

		const newBtn = page.getByTestId('dia-new-demand-button');
		await expect(newBtn).toBeVisible({ timeout: 30_000 });
		await newBtn.click();

		await expect(page.getByTestId('dia-demand-drawer')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('dia-landing-page')).toBeVisible();
		const frame = drawerFrame(page);
		await expect(frame.getByTestId('dia-builder-page')).toBeVisible({ timeout: 60_000 });
		await expect(frame.getByTestId('dia-builder-stepper')).toBeVisible();
		await expect(frame.getByTestId('dia-builder-step-identity')).toBeVisible();

		const sidebar = page.locator('.sidebar-item-label', { hasText: 'Strategy Alignment' });
		await expect(sidebar.first()).toBeVisible({ timeout: 30_000 });
		await expect(
			page.locator('.sidebar-item-label', { hasText: 'Demand Intake & Approval' }).first(),
		).toBeVisible();

		await page.getByTestId('dia-demand-drawer-close').click();
		await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 30_000 });
	});
});
