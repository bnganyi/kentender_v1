import { expect, test } from '@playwright/test';

import { loginAsProcurementPlanner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

test.describe('DIA planning readiness panel', () => {
	test('approved demand shows blocker table and confirm action when ready', async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await openDIALanding(page);

		await page.getByTestId('dia-tab-approved').click();
		const row = page.getByTestId('dia-row-DIA-PE-MOH-2026-0001');
		const hasSeed = await row.isVisible({ timeout: 25_000 }).catch(() => false);
		test.skip(!hasSeed, 'Seed DIA-PE-MOH-2026-0001 not present in Approved queue.');

		await row.click();
		await page.getByTestId('dia-tab-planning').click();
		await expect(page.getByTestId('dia-planning-panel')).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId('dia-planning-blocker-table')).toBeVisible({
			timeout: 20_000,
		});
		await expect(page.getByTestId('dia-planning-check-row-budget_line')).toContainText('Budget line');
		await expect(page.getByTestId('dia-planning-readiness-ready')).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId('dia-action-mark-planning-ready')).toHaveText(/Confirm Planning Ready/i);
	});
});
