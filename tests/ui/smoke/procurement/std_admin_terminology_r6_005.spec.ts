/**
 * R6-005 / LV-R6-005-01 — STD Admin terminology protection: Official STD Library governance
 * copy remains primary for administrators; TM2 business-readiness simplification must not
 * replace or overlay this shell.
 *
 * Companion: docs/prompts/0. usability handoff/R6_005_std_admin_terminology_protection_evidence.md
 */
import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';

test.describe('STD Admin official library terminology (R6-005)', () => {
	test('PLC-R6-005-01: Administrator sees governance-first Official STD Library shell (no TM2 readiness overlay)', async ({
		page,
		baseURL,
	}) => {
		await loginAsAdministrator(page);

		const root = baseURL ?? '';
		await page.goto(`${root}/app/std-engine/library`, { waitUntil: 'domcontentloaded' });

		const shell = page.getByTestId('std-library-page');
		await expect(shell).toBeVisible({ timeout: 90_000 });

		await expect(page.getByTestId('std-library-header-title')).toContainText(/Official STD Library/i, {
			timeout: 45_000,
		});

		await expect(page.getByTestId('std-library-header-subtitle')).toContainText(
			/manage official standard tender documents/i,
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

		// Queue summary cards retain STD-library governance labels (§12.5 — primary admin concept).
		await expect(page.getByTestId('std-library-card-active')).toContainText(/Active STDs/i);
		await expect(page.getByTestId('std-library-card-package-imports')).toContainText(/Package Imports/i);

		await expect(page.getByTestId('std-library-create-instance-button-absent')).toBeAttached();

		// R6 TM2 business-readiness must not bleed into the STD Admin page shell.
		await expect(shell.locator('[data-testid="plc-business-readiness-summary"]')).toHaveCount(0);
		await expect(shell.getByText(/Tender document readiness/i)).toHaveCount(0);

		await expect(page).toHaveURL(/std-engine/i, { timeout: 15_000 });
		await expect(page).not.toHaveURL(/tender-management(?:-|$)/i);
	});
});
