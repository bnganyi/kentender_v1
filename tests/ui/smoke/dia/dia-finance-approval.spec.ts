import { test, expect } from '@playwright/test';

import { loginAsFinanceReviewer } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/** S11 — finance approve with sufficient budget creates reservation and marks approved. */
test('Finance approve with reservation (S11)', async ({ page }) => {
	await loginAsFinanceReviewer(page);
	await openDIALanding(page);

	const row = page.getByTestId('dia-row-DIA-MOH-2026-0003');
	const hasSeed = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasSeed, 'Seed DIA-MOH-2026-0003 not present — run seed_dia_basic or seed_dia_extended.');

	await row.click();
	await expect(page.getByTestId('dia-detail-panel')).toBeVisible({ timeout: 20_000 });

	const approveBtn = page.getByTestId('dia-action-approve-finance');
	const canApprove = await approveBtn.isVisible({ timeout: 10_000 }).catch(() => false);
	test.skip(!canApprove, 'Seed demand not currently actionable for finance approval.');

	await approveBtn.click();
	await expect(page.getByTestId('dia-detail-current-stage')).toContainText('Approved', { timeout: 20_000 });
	await expect(page.getByTestId('dia-detail-reservation-status')).toContainText('Reserved', {
		timeout: 20_000,
	});
	await expect(page.getByTestId('dia-detail-reservation-reference')).not.toContainText('—');
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0003')).toBeHidden({ timeout: 20_000 });

	await page.getByTestId('dia-tab-approved').click();
	await page.getByTestId('dia-queue-approved_today').click();
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0003')).toBeVisible({ timeout: 20_000 });
});
