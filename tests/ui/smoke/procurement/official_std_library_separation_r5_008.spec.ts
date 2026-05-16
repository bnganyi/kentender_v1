/**
 * R5-008 / LV-R5-008-01 — Official STD Library separation: governance shell is primary `std-engine` surface.
 *
 * Companion evidence doc:
 * docs/prompts/0. usability handoff/R5_008_official_STD_library_separation_evidence.md
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('Official STD Library governance separation (R5-008)', () => {
	test('PLC-R5-008-01: std-engine library presents governance framing and tenders are not hero CTAs', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);

		const root = baseURL ?? '';
		await page.goto(`${root}/app/std-engine/library`, { waitUntil: 'domcontentloaded' });

		await expect(page.getByTestId('std-library-page')).toBeVisible({ timeout: 90_000 });

		await expect(page.getByTestId('std-library-header-title')).toContainText(/Official STD Library/i, {
			timeout: 45_000,
		});

		await expect(page.getByTestId('std-library-header-subtitle')).toContainText(
			/manage official standard tender documents|official standard tender documents/i,
			{ timeout: 45_000 },
		);

		await expect(page.getByTestId('std-library-guidance-strip')).toContainText(/structured packages/i, {
			timeout: 45_000,
		});
		await expect(page.getByTestId('std-library-guidance-strip')).toContainText(/immutable/i, {
			timeout: 45_000,
		});

		await expect(page.getByTestId('std-library-import-package-button')).toContainText(
			/Import Official STD Package/i,
		);

		await expect(page.getByTestId('std-library-create-instance-button-absent')).toBeAttached();

		await expect(page).toHaveURL(/std-engine/i, { timeout: 15_000 });
		await expect(page).not.toHaveURL(/tender-management(?:-|$)/i);
	});
});
