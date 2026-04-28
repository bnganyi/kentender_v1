import { test, expect } from '@playwright/test';

import { loginAsFinanceReviewer, loginAsHoDApprover } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/** S6 — HoD approve transitions pending demand into finance queue. */
test('HoD approve moves demand to finance (S6)', async ({ page }) => {
	await loginAsHoDApprover(page);
	await openDIALanding(page);

	const row = page.getByTestId('dia-row-DIA-MOH-2026-0002');
	const hasSeed = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasSeed, 'Seed DIA-MOH-2026-0002 not present — run seed_dia_basic or seed_dia_extended.');

	await row.click();
	await expect(page.getByTestId('dia-detail-panel')).toBeVisible({ timeout: 20_000 });

	const approveBtn = page.getByTestId('dia-action-approve-hod');
	const canApprove = await approveBtn.isVisible({ timeout: 10_000 }).catch(() => false);
	test.skip(!canApprove, 'Seed demand not currently actionable by HoD (status may already be progressed).');

	await approveBtn.click();
	await expect(page.getByTestId('dia-detail-current-stage')).toContainText('Pending Finance Approval', {
		timeout: 20_000,
	});
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0002')).toBeHidden({ timeout: 20_000 });

	await loginAsFinanceReviewer(page);
	await openDIALanding(page);
	await expect(page.getByTestId('dia-queue-pending_finance')).toBeVisible({ timeout: 20_000 });
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0002')).toBeVisible({ timeout: 20_000 });
});
