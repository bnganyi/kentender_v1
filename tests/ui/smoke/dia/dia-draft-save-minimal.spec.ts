import { expect, test } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

function drawerFrame(page) {
	return page.frameLocator('[data-testid="dia-demand-drawer-frame"]');
}

test.describe('DIA draft save — title only', () => {
	test('new demand drawer saves with title only', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);

		await page.getByTestId('dia-new-demand-button').click();
		await expect(page.getByTestId('dia-demand-drawer')).toBeVisible({ timeout: 60_000 });
		const frame = drawerFrame(page);
		await expect(frame.getByTestId('dia-builder-page')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByTestId('dia-landing-page')).toBeVisible();

		const title = `PW Draft ${Date.now()}`;
		await frame.locator('[data-fieldname="title"] input').fill(title);
		await frame.getByTestId('dia-builder-save-draft').click();

		await expect(frame.locator('.msgprint')).toHaveCount(0, { timeout: 15_000 });
		await expect(frame.getByText('Saved', { exact: true })).toBeVisible({ timeout: 15_000 });
		await expect(frame.locator('[data-fieldname="title"] input')).toHaveValue(title);
		await expect(frame.locator('.form-section[data-fieldname="section_items"]')).toBeHidden();
	});
});
