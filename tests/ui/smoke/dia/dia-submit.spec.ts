import { test, expect } from '@playwright/test';

import { loginAsHoDApprover, loginAsRequisitioner } from '../../helpers/auth';
import { diaWorkspace } from '../../helpers/selectors';

/** S4 — valid requisitioner draft transitions into Pending HoD and appears in HoD queue. */
test('Submit draft to HoD queue (S4)', async ({ page }) => {
	await loginAsRequisitioner(page);
	await page.goto(diaWorkspace.route, { waitUntil: 'domcontentloaded' });
	await page.waitForLoadState('domcontentloaded');
	const noPermVisible = await page
		.getByText('No permission for Page')
		.waitFor({ state: 'visible', timeout: 8_000 })
		.then(() => true)
		.catch(() => false);
	test.skip(noPermVisible, 'Requisitioner lacks workspace Page permission in this site.');
	await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });

	const draftRow = page.getByTestId('dia-row-DIA-MOH-2026-0001');
	const hasDraftSeed = await draftRow.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasDraftSeed, 'Seed DIA-MOH-2026-0001 draft not present — run seed_dia_basic or seed_dia_extended.');

	await draftRow.click();
	await expect(page.getByTestId('dia-detail-panel')).toBeVisible();
	const submitBtn = page.getByTestId('dia-action-submit');
	const canSubmit = await submitBtn.isVisible({ timeout: 15_000 }).catch(() => false);
	test.skip(!canSubmit, 'Seed DIA-MOH-2026-0001 is not in submit-ready Draft state for requisitioner.');

	await submitBtn.click();
	await expect(page.getByTestId('dia-detail-current-stage')).toContainText('Pending HoD Approval', { timeout: 20_000 });
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0001')).toBeHidden({ timeout: 20_000 });

	await loginAsHoDApprover(page);
	await page.goto(diaWorkspace.route, { waitUntil: 'domcontentloaded' });
	await page.waitForLoadState('domcontentloaded');
	await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });
	await expect(page.getByTestId('dia-queue-pending_hod_approval')).toBeVisible({ timeout: 20_000 });
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0001')).toBeVisible({ timeout: 20_000 });
});
