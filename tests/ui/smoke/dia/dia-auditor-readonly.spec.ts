import { test, expect } from '@playwright/test';

import { loginAsAuditor } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

/** Auditor read-only smoke: can view queues/details but cannot perform workflow mutations. */
test('Auditor has read-only DIA access', async ({ page }) => {
	test.skip(!process.env.UI_AUDITOR_USER, 'Set UI_AUDITOR_USER/UI_AUDITOR_PASSWORD for auditor smoke.');

	await loginAsAuditor(page);
	await openDIALanding(page);

	await page.getByTestId('dia-tab-all').click();
	await page.getByTestId('dia-queue-all_demands').click();
	await expect(page.getByTestId('dia-list-root')).toBeVisible({ timeout: 25_000 });

	const row = page.getByTestId('dia-row-DIA-MOH-2026-0002');
	const hasSeed = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasSeed, 'Seed DIA-MOH-2026-0002 not present — run seed_dia_basic or seed_dia_extended.');

	await row.click();
	await expect(page.getByTestId('dia-detail-panel')).toBeVisible();
	await expect(page.getByTestId('dia-action-submit')).toHaveCount(0);
	await expect(page.getByTestId('dia-action-approve-hod')).toHaveCount(0);
	await expect(page.getByTestId('dia-action-approve-finance')).toHaveCount(0);
	await expect(page.getByTestId('dia-action-return')).toHaveCount(0);
	await expect(page.getByTestId('dia-action-reject')).toHaveCount(0);
	await expect(page.getByTestId('dia-action-cancel')).toHaveCount(0);
	await expect(page.getByTestId('dia-action-mark-planning-ready')).toHaveCount(0);
	await expect(page.getByRole('button', { name: 'View demand' })).toBeVisible();
});
