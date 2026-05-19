/**
 * Compact lifecycle queue bar — inline grouped stages (no nested cards).
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { dismissOptionalDeskModals } from '../../helpers/routes';

test.describe('TM2 compact lifecycle queue bar', () => {
	test.setTimeout(120_000);

	test('uses inline stage rows without group cards; chips show counts', async ({ page, baseURL }) => {
		await loginAsAdministrator(page);
		const root = (baseURL || 'http://127.0.0.1:8000').replace(/\/$/, '');
		await page.goto(`${root}/app/tender-management-v2`);
		await page.waitForLoadState('domcontentloaded');
		await dismissOptionalDeskModals(page);

		const bar = page.getByTestId('tm2-lifecycle-bar');
		await expect(bar).toBeVisible({ timeout: 90_000 });

		await expect(bar.locator('.tm2-lifecycle-stage-panel')).toHaveCount(0);

		await expect(bar.getByTestId('tm2-lifecycle-stage-row-primary')).toBeVisible();
		await expect(bar.getByTestId('tm2-lifecycle-stage-row-closing')).toBeVisible();

		await expect(bar.getByTestId('tm2-lifecycle-stage-preparation')).toContainText('Preparation');
		await expect(bar.getByTestId('tm2-lifecycle-stage-review')).toContainText('Review');
		await expect(bar.getByTestId('tm2-lifecycle-stage-live_tender')).toContainText('Live Tender');
		await expect(bar.getByTestId('tm2-lifecycle-stage-closing')).toContainText('Closing');

		await expect(bar.getByText('Review & Publication')).toHaveCount(0);
		await expect(bar.getByText('Closing & Handoff')).toHaveCount(0);

		await expect(bar.getByTestId('tm2-queue-draft')).toHaveText(/\bDraft\s+\d+$/);
		await expect(bar.getByTestId('tm2-queue-std-incomplete')).toHaveText(/\bDoc incomplete\s+\d+$/);
		await expect(bar.getByTestId('tm2-lifecycle-all')).toHaveText(/\bAll\s+\d+$/);

		const box = await bar.boundingBox();
		expect(box?.height || 0).toBeLessThanOrEqual(130);
	});
});
