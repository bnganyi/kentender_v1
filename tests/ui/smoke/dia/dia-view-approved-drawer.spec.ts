import { expect, test } from '@playwright/test';

import { loginAsRequisitioner } from '../../helpers/auth';
import { openDIALanding } from '../../helpers/dia';

function drawerFrame(page) {
	return page.frameLocator('[data-testid="dia-demand-drawer-frame"]');
}

test.describe('DIA view approved demand drawer', () => {
	test('approved demand shows step content with read-only navigation', async ({ page }) => {
		await loginAsRequisitioner(page);
		await openDIALanding(page);

		await page.getByTestId('dia-tab-approved').click();
		const seededRow = page.getByTestId('dia-row-DIA-PE-MOH-2026-0001');
		const fallbackRow = page.locator('[data-testid^="dia-row-"]').first();
		const hasSeed = await seededRow.isVisible({ timeout: 25_000 }).catch(() => false);
		const row = hasSeed ? seededRow : fallbackRow;
		const hasApproved = await row.isVisible({ timeout: 5_000 }).catch(() => false);
		test.skip(!hasApproved, 'No approved demand visible in Approved queue.');

		await row.click();
		await expect(page.getByTestId('dia-detail-panel')).toBeVisible({ timeout: 20_000 });

		await page.getByTestId('dia-action-edit').click();
		await expect(page.getByTestId('dia-demand-drawer')).toBeVisible({ timeout: 60_000 });
		await expect(page.getByRole('heading', { name: 'View Demand' })).toBeVisible();

		const frame = drawerFrame(page);
		await expect(frame.getByTestId('dia-builder-page')).toBeVisible({ timeout: 60_000 });
		await expect(frame.getByTestId('dia-builder-readonly-badge')).toContainText('Approved');
		await expect(frame.getByTestId('dia-builder-save-draft')).toHaveCount(0);
		await expect(frame.getByTestId('dia-builder-readonly-notice')).toHaveCount(0);

		await frame.getByTestId('dia-builder-step-items').click();
		await expect(frame.locator('.form-section[data-fieldname="section_items"]')).toBeVisible();
		await expect(frame.locator('.form-section[data-fieldname="section_identifiers"]')).toBeHidden();

		await frame.getByTestId('dia-builder-step-justification').click();
		await expect(frame.locator('.form-section[data-fieldname="section_justification_delivery"]')).toBeVisible();
		await expect(
			frame.locator('.form-section[data-fieldname="section_justification_delivery"]'),
		).toContainText('Business justification');
		await expect(frame.locator('.form-section[data-fieldname="section_workflow_state"]')).toBeHidden();
	});
});
