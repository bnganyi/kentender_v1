import { test, expect } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding, expectDiaShellVisible } from '../../helpers/dia';

test.describe('DIA landing shell (H2 testids)', () => {
	test('tabs, filters, and KPI strip expose stable selectors', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);
		await expectDiaShellVisible(page);
		await expect(page.getByTestId('dia-tab-my-work')).toBeVisible();
		await expect(page.getByTestId('dia-tab-all')).toBeVisible();
		await expect(page.getByTestId('dia-tab-approved')).toBeVisible();
		await expect(page.getByTestId('dia-tab-rejected')).toBeVisible();
		await expect(page.getByTestId('dia-filter-date-range')).toBeVisible();
		await expect(page.getByTestId('dia-filter-demand-type')).toBeVisible();
		await expect(page.getByTestId('dia-filter-department')).toBeVisible();
		await expect(page.getByTestId('dia-filter-budget-line')).toBeVisible();
		await expect(page.getByTestId('dia-filter-priority')).toBeVisible();
		await expect(page.getByTestId('dia-new-demand-button')).toBeVisible();
	});
});
