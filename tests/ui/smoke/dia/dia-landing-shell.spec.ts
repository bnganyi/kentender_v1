import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding, expectDiaShellVisible } from '../../helpers/dia';

test.describe('DIA landing shell (H2 testids)', () => {
	test('status chips, list head filters, and header expose stable selectors', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);
		await expectDiaShellVisible(page);
		await expect(page.getByTestId('dia-status-chips')).toBeVisible();
		await expect(page.getByTestId('dia-tab-all')).toBeVisible();
		await expect(page.getByTestId('dia-tab-my-work')).toBeVisible();
		await expect(page.getByTestId('dia-tab-draft')).toBeVisible();
		await expect(page.getByTestId('dia-tab-hod')).toBeVisible();
		await expect(page.getByTestId('dia-tab-finance')).toBeVisible();
		await expect(page.getByTestId('dia-tab-cancelled')).toBeVisible();
		await expect(page.getByTestId('dia-tab-not-yet-planned')).toHaveCount(0);
		await expect(page.getByTestId('dia-list-head')).toBeVisible();
		await expect(page.getByTestId('dia-search')).toBeVisible();
		await page.getByTestId('dia-filters-toggle').click();
		await expect(page.getByTestId('dia-filter-date-range')).toBeVisible();
		await expect(page.getByTestId('dia-filter-demand-type')).toBeVisible();
		await expect(page.getByTestId('dia-filter-department')).toBeVisible();
		await expect(page.getByTestId('dia-filter-budget-line')).toBeVisible();
		await expect(page.getByTestId('dia-filter-priority')).toBeVisible();
		await expect(page.getByTestId('dia-new-demand-button')).toBeVisible();
	});
});
