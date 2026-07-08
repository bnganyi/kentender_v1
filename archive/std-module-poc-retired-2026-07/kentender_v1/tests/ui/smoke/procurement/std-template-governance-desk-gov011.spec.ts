import { expect, test } from '@playwright/test';

import { loginAsAdministrator } from '../../helpers/auth';
import { STD_ADMIN_TEMPLATE_CODE, expectStdGovernanceGroupVisible } from '../../helpers/stdAdminConsoleDesk';

test.describe('STD Template — STD Governance Desk (GOV-011)', () => {
	test.setTimeout(120_000);

	test('STD Template form exposes STD Governance action group', async ({ page }) => {
		await loginAsAdministrator(page);

		await page.goto(`/app/std-template/${encodeURIComponent(STD_ADMIN_TEMPLATE_CODE)}`, {
			waitUntil: 'domcontentloaded',
		});

		await expectStdGovernanceGroupVisible(page);

		const group = page
			.locator(`.inner-group-button[data-label="${encodeURIComponent('STD Governance')}"]`)
			.first();
		await group.locator('button').first().click();

		await expect(
			page.locator('.dropdown-menu.show a.dropdown-item').filter({ hasText: 'View Governance Summary' }),
		).toBeVisible({ timeout: 15_000 });
	});
});
