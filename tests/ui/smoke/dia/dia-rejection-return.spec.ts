import { test, expect } from '@playwright/test';

import { loginAsHoDApprover, loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding, openDiaReviewTab } from '../../helpers/dia';

/** S8 — HoD returns pending demand to draft with reason; owner sees it in returned queue. */
test('HoD return to draft with reason (S8)', async ({ page }) => {
	await loginAsHoDApprover(page);
	await openDIALanding(page);

	const row = page.getByTestId('dia-row-DIA-MOH-2026-0002');
	const hasSeed = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasSeed, 'Seed DIA-MOH-2026-0002 not present — run seed_dia_basic or seed_dia_extended.');

	await row.click();
	await expect(page.getByTestId('dia-detail-panel')).toBeVisible({ timeout: 20_000 });
	await openDiaReviewTab(page);
	const returnBtn = page.getByTestId('dia-action-return');
	const canReturn = await returnBtn.isVisible({ timeout: 10_000 }).catch(() => false);
	test.skip(!canReturn, 'Seed demand not currently actionable for HoD return.');

	await returnBtn.click();
	const modal = page.locator('div.modal.show[role="dialog"]');
	await modal.locator('textarea, input[type="text"]').first().fill('Please revise quantities and scope.');
	await modal.getByRole('button', { name: /^Return$/i }).click();
	await page.getByTestId('dia-tab-overview').click();
	await expect(page.getByTestId('dia-detail-current-stage')).toContainText('Returned', { timeout: 20_000 });
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0002')).toBeHidden({ timeout: 20_000 });

	await loginAsRequisitioner(page);
	await openDIALanding(page);
	await page.getByTestId('dia-tab-my-work').click();
	await page.getByTestId('dia-tab-draft').click();
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0002')).toBeVisible({ timeout: 20_000 });
});
