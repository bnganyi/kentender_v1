import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding, expectDiaShellVisible } from '../../helpers/dia';

/**
 * S1 — Empty-state friendly landing (see DIA Smoke Test Contract §8).
 * Best run after `bench execute ...seed_dia_empty` on a site with no other demands in the active queue.
 */
test.describe('DIA empty / landing shell', () => {
	test('requisitioner sees workbench shell and queue area', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);
		await expectDiaShellVisible(page);
		await expect(page.getByTestId('dia-work-tabs')).toBeVisible();
		await expect(page.getByTestId('dia-queue-selector')).toBeVisible();
		await expect(page.getByTestId('dia-kpi-my-drafts')).toBeVisible();
		const queueSurface = page.getByTestId('dia-list-empty').or(page.getByTestId('dia-list'));
		await expect(queueSurface.first()).toBeVisible({ timeout: 30_000 });
	});
});
