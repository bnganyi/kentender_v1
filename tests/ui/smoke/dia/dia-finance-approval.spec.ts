import { test, expect } from '@playwright/test';

import { loginAsFinanceReviewer } from '../../helpers/auth';
import { diaWorkspace } from '../../helpers/selectors';

/** S11 — finance approve with sufficient budget creates reservation and marks approved. */
test('Finance approve with reservation (S11)', async ({ page }) => {
	await loginAsFinanceReviewer(page);
	await page.goto(diaWorkspace.route, { waitUntil: 'domcontentloaded' });
	await page.waitForLoadState('domcontentloaded');

	const noPermVisible = await page
		.getByText('No permission for Page')
		.waitFor({ state: 'visible', timeout: 8_000 })
		.then(() => true)
		.catch(() => false);
	test.skip(noPermVisible, 'Finance user lacks workspace Page permission in this site.');
	await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });

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
