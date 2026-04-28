import { test, expect } from '@playwright/test';

import { login } from '../../helpers/auth';
import { navigateToDiaWorkspace } from '../../helpers/dia';

/** S22 — non-DIA role is blocked from actionable DIA workbench usage. */
test('Non-DIA role cannot access workbench actions (S22)', async ({ page }) => {
	test.skip(
		!process.env.UI_NON_DIA_USER || !process.env.UI_NON_DIA_PASSWORD,
		'Set UI_NON_DIA_USER/UI_NON_DIA_PASSWORD for a non-DIA role account.',
	);
	await login(page, process.env.UI_NON_DIA_USER || '', process.env.UI_NON_DIA_PASSWORD || '');
	await navigateToDiaWorkspace(page);

	const noPagePerm = page.getByText('No permission for Page');
	const landingBlocked = page.getByTestId('dia-landing-blocked');
	await expect(noPagePerm.or(landingBlocked)).toBeVisible({ timeout: 20_000 });

	// If shell injects, it must still be blocked and non-actionable.
	const blockedVisible = await landingBlocked.isVisible().catch(() => false);
	if (blockedVisible) {
		await expect(landingBlocked).toContainText('Demand Intake');
		await expect(landingBlocked).toContainText('assign a Demand Intake role');
		await expect(page.getByTestId('dia-new-demand-button')).toHaveCount(0);
		await expect(page.getByTestId('dia-list-root')).toHaveCount(1);
	}
});
