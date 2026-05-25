import { expect, test } from '@playwright/test';

import { loginAsProcurementPlanner } from '../../helpers/auth';
import { openDIALanding, openDiaReviewTab } from '../../helpers/dia';

test.describe('DIA review tab state-aware', () => {
	test('approved demand shows approval outcome, not submission ready', async ({ page }) => {
		await loginAsProcurementPlanner(page);
		await openDIALanding(page);

		await page.getByTestId('dia-tab-approved').click();
		const row = page.getByTestId('dia-row-DIA-PE-MOH-2026-0001');
		const hasSeed = await row.isVisible({ timeout: 25_000 }).catch(() => false);
		test.skip(!hasSeed, 'Seed DIA-PE-MOH-2026-0001 not present in Approved queue.');

		await row.click();
		await openDiaReviewTab(page);

		await expect(page.getByTestId('dia-review-approval-outcome')).toBeVisible({ timeout: 20_000 });
		await expect(page.getByTestId('dia-review-submission-ready')).toHaveCount(0);
		await expect(page.getByTestId('dia-review-planning-guidance')).toBeVisible();
	});
});
