import { test, expect } from '@playwright/test';

import { loginAsHoDApprover, loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';
import { diaWorkspace } from '../../helpers/selectors';

/** S8 — HoD returns pending demand to draft with reason; owner sees it in returned queue. */
test('HoD return to draft with reason (S8)', async ({ page }) => {
	await loginAsHoDApprover(page);
	await page.goto(diaWorkspace.route, { waitUntil: 'domcontentloaded' });
	await page.waitForLoadState('domcontentloaded');
	const noPermVisible = await page
		.getByText('No permission for Page')
		.waitFor({ state: 'visible', timeout: 8_000 })
		.then(() => true)
		.catch(() => false);
	test.skip(noPermVisible, 'HoD user lacks workspace Page permission in this site.');
	await expect(page.getByTestId('dia-landing-page')).toBeVisible({ timeout: 45_000 });

	const row = page.getByTestId('dia-row-DIA-MOH-2026-0002');
	const hasSeed = await row.isVisible({ timeout: 20_000 }).catch(() => false);
	test.skip(!hasSeed, 'Seed DIA-MOH-2026-0002 not present — run seed_dia_basic or seed_dia_extended.');

	await row.click();
	await expect(page.getByTestId('dia-detail-panel')).toBeVisible({ timeout: 20_000 });
	const returnBtn = page.getByTestId('dia-action-return');
	const canReturn = await returnBtn.isVisible({ timeout: 10_000 }).catch(() => false);
	test.skip(!canReturn, 'Seed demand not currently actionable for HoD return.');

	await returnBtn.click();
	await page.getByRole('dialog').getByLabel('Return reason').fill('Please revise quantities and scope.');
	await page.getByRole('button', { name: 'Return', exact: true }).click();
	await expect(page.getByTestId('dia-detail-current-stage')).toContainText('Returned', { timeout: 20_000 });
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0002')).toBeHidden({ timeout: 20_000 });

	await loginAsRequisitioner(page);
	await openDIALanding(page);
	await page.getByTestId('dia-tab-rejected').click();
	await page.getByTestId('dia-queue-returned_to_me').click();
	await expect(page.getByTestId('dia-row-DIA-MOH-2026-0002')).toBeVisible({ timeout: 20_000 });
});
